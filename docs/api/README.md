# API Documentation

This section documents the key interfaces and components.

## Core Modules

### Audio Processing
The `CombinedProcessor` class handles audio processing and transcription.

### Analysis
- `TopicAnalyzer`: Extracts and organizes discussion topics
- `ArgumentAnalyzer`: Identifies argument structures and relationships
- `SentimentAnalyzer`: Analyzes emotional tone throughout the discussion

### Storage
- `SQLiteDAO`: Provides data access to the SQLite database
- `LocalFileStorage`: Manages file storage for audio files and reports
