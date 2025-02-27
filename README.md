# Discussion Analysis System

An AI-powered pipeline that analyzes meeting/discussion recordings to:
- Transcribe audio with speaker diarization
- Perform topic and sentiment analysis 
- Generate interactive HTML reports with visualizations

Key Components:
- Audio Processor (Whisper + Pyannote)
- LLM Analysis (Together.ai Llama 3.1 70B)
- SQLite Storage
- CLI Interface
- D3.js Visualizations