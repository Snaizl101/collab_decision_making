from pathlib import Path
from typing import Optional, List, Dict
from dataclasses import dataclass
from stable_whisper import load_model
from pydub import AudioSegment
from .base import AudioProcessor, AudioMetadata, ProcessingConfig, DiarizationResult, SpeakerSegment, \
    AudioProcessingError


@dataclass
class TranscriptionSegment:
    text: str
    start: float
    end: float
    speaker: str
    confidence: float


class StableAudioProcessor(AudioProcessor):
    def __init__(self, model_size: str = "base"):
        """Initialize with specified model size (tiny, base, small, medium, large)"""
        try:
            self.model = load_model(model_size)
        except Exception as e:
            raise AudioProcessingError(f"Failed to load stable-ts model: {str(e)}")

    def preprocess_audio(self,
                         input_file: Path,
                         config: ProcessingConfig) -> Path:
        """Preprocess audio file to match required specifications"""
        try:
            # Load audio
            audio = AudioSegment.from_file(str(input_file))

            # Apply audio preprocessing
            audio = (audio
                     .set_frame_rate(config.target_sample_rate)
                     .set_channels(config.target_channels)
                     .normalize())  # Normalize audio levels

            # Create temporary processed file
            temp_path = input_file.parent / f"temp_processed_{input_file.name}"

            # Export with specific format
            audio.export(
                temp_path,
                format=config.target_format,
                parameters=["-ac", "1", "-ar", "16000"]
            )

            return temp_path

        except Exception as e:
            raise AudioProcessingError(f"Audio preprocessing failed: {str(e)}")

    def process(self,
                input_file: Path,
                output_dir: Path,
                config: Optional[ProcessingConfig] = None,
                progress_callback: Optional[callable] = None) -> Dict[str, any]:
        """Process audio file with combined transcription and diarization"""
        if not self.validate_file(input_file):
            raise AudioProcessingError(f"Invalid audio file: {input_file}")

        # Use default config if none provided
        config = config or ProcessingConfig()

        try:
            # Preprocess audio
            if progress_callback:
                progress_callback(0.1, "Preprocessing audio...")

            processed_audio = self.preprocess_audio(input_file, config)

            if progress_callback:
                progress_callback(0.3, "Starting transcription and diarization...")

            # Process with stable-ts
            result = self.model.transcribe(
                str(processed_audio),
                word_timestamps=True,
                vad=True,
                detect_disfluencies=True
            )

            if progress_callback:
                progress_callback(0.7, "Processing results...")

            # Convert result to our data structure
            segments = []
            speaker_segments = []
            current_speaker = None
            segment_start = None

            for word in result.segments:
                if word.speaker != current_speaker:
                    if segment_start is not None:
                        speaker_segments.append(
                            SpeakerSegment(
                                start_time=segment_start,
                                end_time=word.start,
                                speaker_id=current_speaker
                            )
                        )
                    current_speaker = word.speaker
                    segment_start = word.start

                segments.append(
                    TranscriptionSegment(
                        text=word.text,
                        start=word.start,
                        end=word.end,
                        speaker=word.speaker,
                        confidence=word.confidence
                    )
                )

            # Add final speaker segment
            if segment_start is not None:
                speaker_segments.append(
                    SpeakerSegment(
                        start_time=segment_start,
                        end_time=segments[-1].end,
                        speaker_id=current_speaker
                    )
                )

            diarization_result = DiarizationResult(
                segments=speaker_segments,
                total_speakers=len(set(seg.speaker_id for seg in speaker_segments)),
                processed_audio=processed_audio
            )

            if progress_callback:
                progress_callback(1.0, "Processing complete")

            return {
                'processed_audio': processed_audio,
                'transcription': segments,
                'diarization': diarization_result
            }

        except Exception as e:
            raise AudioProcessingError(f"Processing failed: {str(e)}")
        finally:
            # Cleanup temporary processed file if it exists
            if 'processed_audio' in locals():
                processed_audio.unlink(missing_ok=True)

    def get_metadata(self, audio_file: Path) -> AudioMetadata:
        """Extract metadata from audio file"""
        try:
            audio = AudioSegment.from_file(str(audio_file))
            return AudioMetadata(
                duration=len(audio) / 1000.0,  # Convert to seconds
                format=audio_file.suffix[1:],  # Remove the dot
                sample_rate=audio.frame_rate,
                channels=audio.channels,
                file_size=audio_file.stat().st_size
            )
        except Exception as e:
            raise AudioProcessingError(f"Metadata extraction failed: {str(e)}")

    def validate_file(self, file_path: Path) -> bool:
        """Validate audio file format and existence"""
        if not file_path.exists():
            return False

        SUPPORTED_FORMATS = {'.wav', '.mp3', '.m4a', '.flac'}
        return file_path.suffix.lower() in SUPPORTED_FORMATS