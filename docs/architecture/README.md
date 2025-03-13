# System Architecture

The Discussion Analysis System follows a layered architecture:

## Architecture Diagram
See system_architecture.html for the complete visual representation.

## Layer Overview

### Presentation Layer
- Command Line Interface: Entry point for user interaction
- Report Generation: Creates HTML reports with visualizations

### Business Layer
- Audio Processing: Handles audio file preprocessing
- Transcription: Converts audio to text with speaker diarization
- Analysis Modules:
  - Topic Analysis: Identifies main discussion topics
  - Sentiment Analysis: Analyzes sentiment of the converstation/discussion per speaker, overtime and overall.
### Storage Layer
- SQLite Database: Stores all analysis results and relationships
- File Storage: Manages audio files and generated reports
