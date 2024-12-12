"""
Requirements:
    - Process different audio formats (WAV, MP3, M4A)
    - Extract metadata (duration, time, format specs, speakers)
    - Save audio files
    - Handle multi-speaker audio
    - Interface with the transcription system
    - Track processing status
"""

from abc import ABC, abstractmethod
