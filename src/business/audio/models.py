from dataclasses import dataclass
from typing import List


@dataclass
class AudioMetadata:
    """Essential metadata for audio files"""
    duration: float
    format: str
    sample_rate: int
    channels: int
    file_size: int


@dataclass
class SpeakerSegment:
    """Represents a segment of speech from a single speaker"""
    start_time: float
    end_time: float
    speaker_id: str
    text: str


@dataclass
class TranscriptionSegment:
    """Individual transcription segment with timestamp"""
    text: str
    start: float
    end: float
    speaker: str
    confidence: float = 1.0


@dataclass
class ProcessingConfig:
    """Configuration for audio processing"""
    target_format: str = "wav"
    target_sample_rate: int = 16000
    target_channels: int = 1


@dataclass
class ProcessingResult:
    """Results of audio processing and transcription

    Attributes:
        metadata: Technical information about the processed audio
        transcription_segments: Word-level transcription with timing
        speaker_segments: Speaker-level segments with complete utterances
        total_speakers: Number of unique speakers detected
    """
    metadata: AudioMetadata
    transcription_segments: List[TranscriptionSegment]
    speaker_segments: List[SpeakerSegment]
    total_speakers: int
