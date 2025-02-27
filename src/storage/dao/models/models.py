from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
from business.audio.models import AudioMetadata, TranscriptionSegment


@dataclass
class Recording:
    """Database model for storing recording information"""
    recording_id: str
    file_path: Path
    metadata: AudioMetadata
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Topic:
    """Database model for discussion topics"""
    topic_id: Optional[int]  # Optional as it's auto-assigned by DB
    recording_id: str
    name: str
    start_time: float
    end_time: float


# @dataclass
# class Argument:
#     """Database model for arguments made during discussion"""
#     argument_id: Optional[int]
#     recording_id: str
#     topic_id: int
#     speaker_id: str
#     text: str
#     start_time: float
#     end_time: float
#     type: str  # e.g., 'support', 'counter', 'clarification'


# @dataclass
# class Agreement:
#     """Database model for tracking agreements/disagreements"""
#     agreement_id: Optional[int]
#     recording_id: str
#     argument_id: int
#     speaker_id: str
#     type: str  # 'agree' or 'disagree'
#     timestamp: float


# @dataclass
# class Gap:
#     """Database model for identified discussion gaps"""
#     gap_id: Optional[int]
#     recording_id: str
#     topic_id: Optional[int]
#     description: str
#     type: str  # e.g., 'missing_viewpoint', 'unclear_conclusion'
