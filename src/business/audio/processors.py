from pathlib import Path
from typing import Optional, List, Dict, Any
from stable_whisper import load_model
from pyannote.audio import Pipeline
from pyannote.audio import Audio
import torch
from pydub import AudioSegment
from .models import AudioMetadata, TranscriptionSegment, SpeakerSegment, ProcessingConfig, ProcessingResult
from .exceptions import ProcessingError


class CombinedProcessor:
    """Handles audio processing using stable-ts for transcription and pyannote.audio for diarization.

    Key Features:
    - Transcribes audio to text
    - Identifies different speakers
    - Handles audio preprocessing and format conversion

    Input: Audio file (WAV, MP3, M4A)
    Output: ProcessingResult with transcription segments and metadata
    """

    def __init__(self, stable_model_size: str = "base", auth_token: Optional[str] = None):
        """
        Initialize with specified stable-ts model size.

        Args:
            stable_model_size: Size of stable-ts model (tiny, base, small, medium, large)
        """
        try:
            # Initialize stable-ts
            self.transcriber = load_model(stable_model_size)

            # Initialize pyannote pipeline
            self.diarizer = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=auth_token
            )

            # Initialize audio loader
            self.audio = Audio()

            # Use GPU if available
            if torch.cuda.is_available():
                self.diarizer = self.diarizer.to(torch.device("cuda"))

        except Exception as e:
            raise ProcessingError(
                message="Failed to load models",
                error_type="initialization",
                original_error=e
            )

    def process_audio(self,
                      audio_path: Path,
                      config: Optional[ProcessingConfig] = None,
                      progress_callback: Optional[callable] = None) -> ProcessingResult:
        """
        Process audio file with transcription and speaker diarization.

        Args:
            audio_path: Path to input audio file
            config: Processing configuration settings
            progress_callback: Optional callback function(progress: float, message: str)

        Returns:
            ProcessingResult containing transcription and metadata
        """
        if not self._validate_file(audio_path):
            raise ProcessingError(
                message=f"Invalid audio file: {audio_path}",
                error_type="validation"
            )

        config = config or ProcessingConfig()
        processed_audio = None

        try:
            # Preprocessing
            if progress_callback:
                progress_callback(0.1, "Preprocessing audio...")

            processed_audio = self.preprocess_audio(audio_path, config)

            # Transcription with stable-ts
            if progress_callback:
                progress_callback(0.3, "Starting transcription...")

            transcription = self.transcriber.transcribe(
                str(processed_audio),
                word_timestamps=True,
                vad=True,
            )

            # Speaker diarization with pyannote
            if progress_callback:
                progress_callback(0.5, "Running speaker diarization...")

            diarization = self.diarizer(str(processed_audio))

            # Combine results
            if progress_callback:
                progress_callback(0.7, "Combining transcription and speaker info...")

            # Create speaker segments from diarization
            speaker_segments = self._create_speaker_segments(diarization)

            # Align transcription with speaker segments
            transcription_segments = self._align_transcription(
                transcription.segments,
                speaker_segments
            )

            # Extract metadata
            metadata = self.get_metadata(audio_path)

            if progress_callback:
                progress_callback(1.0, "Processing complete")

            return ProcessingResult(
                metadata=metadata,
                transcription_segments=transcription_segments,
                speaker_segments=speaker_segments,
                total_speakers=len(set(seg.speaker_id for seg in speaker_segments))
            )

        except Exception as e:
            raise ProcessingError(
                message=f"Processing failed: {str(e)}",
                error_type="processing",
                original_error=e
            )
        finally:
            if processed_audio and Path(processed_audio).exists():
                Path(processed_audio).unlink()

    def _create_speaker_segments(self, diarization) -> List[SpeakerSegment]:
        """Convert pyannote diarization output to speaker segments"""
        segments = []
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            segments.append(SpeakerSegment(
                start_time=turn.start,
                end_time=turn.end,
                speaker_id=speaker,
                text=""  # Will be filled during alignment
            ))
        return sorted(segments, key=lambda x: x.start_time)

    def _align_transcription(self,
                             stable_segments: List[Any],
                             speaker_segments: List[SpeakerSegment]) -> List[TranscriptionSegment]:
        """Align stable-ts transcription with speaker segments"""
        transcription_segments = []

        for word in stable_segments:
            # Find overlapping speaker segment
            start_time = float(word.start)  # Ensure float type
            end_time = float(word.end)  # Ensure float type

            # Find speaker with maximum overlap
            max_overlap = 0
            assigned_speaker = None

            for speaker_seg in speaker_segments:
                overlap_start = max(start_time, speaker_seg.start_time)
                overlap_end = min(end_time, speaker_seg.end_time)

                if overlap_end > overlap_start:
                    overlap_duration = overlap_end - overlap_start
                    if overlap_duration > max_overlap:
                        max_overlap = overlap_duration
                        assigned_speaker = speaker_seg.speaker_id

            # Create transcription segment
            if assigned_speaker:
                transcription_segments.append(TranscriptionSegment(
                    text=str(word.text),
                    start=start_time,
                    end=end_time,
                    speaker=assigned_speaker,
                ))

                # Update speaker segment text
                for seg in speaker_segments:
                    if seg.speaker_id == assigned_speaker and \
                            start_time >= seg.start_time and \
                            end_time <= seg.end_time:
                        seg.text += f" {word.text}"
                        break

        return transcription_segments

    def preprocess_audio(self, input_file: Path, config: ProcessingConfig) -> Path:
        """Preprocess audio file to match required specifications"""
        try:
            audio = AudioSegment.from_file(str(input_file))
            audio = (audio
                     .set_frame_rate(config.target_sample_rate)
                     .set_channels(config.target_channels)
                     .normalize())

            temp_path = input_file.parent / f"temp_processed_{input_file.name}"
            audio.export(
                temp_path,
                format=config.target_format,
                parameters=["-ac", "1", "-ar", "16000"]
            )
            return temp_path

        except Exception as e:
            raise ProcessingError(
                message="Audio preprocessing failed",
                error_type="preprocessing",
                original_error=e
            )

    def get_metadata(self, audio_file: Path) -> AudioMetadata:
        """Extract metadata from audio file"""
        try:
            audio = AudioSegment.from_file(str(audio_file))
            return AudioMetadata(
                duration=len(audio) / 1000.0,
                format=audio_file.suffix[1:],
                sample_rate=audio.frame_rate,
                channels=audio.channels,
                file_size=audio_file.stat().st_size
            )
        except Exception as e:
            raise ProcessingError(
                message="Metadata extraction failed",
                error_type="metadata",
                original_error=e
            )

    def _validate_file(self, file_path: Path) -> bool:
        """Validate audio file format and existence"""
        if not file_path.exists():
            return False
        SUPPORTED_FORMATS = {'.wav', '.mp3', '.m4a', '.flac'}
        return file_path.suffix.lower() in SUPPORTED_FORMATS
