# User Guide

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Set up environment variables:
   ```
   TOGETHER_API_KEY=your_api_key
   ```

## Usage

Basic usage:
```
python -m src.presentation.cli.cli analyze /path/to/audio_file.mp3
```

This will:
1. Process the audio file
2. Generate analysis
3. Create an HTML report in the output directory

For more details, run:
```
python -m src.presentation.cli.cli --help
```

