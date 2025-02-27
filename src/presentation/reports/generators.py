# src/presentation/reports/generators.py

from pathlib import Path
from typing import Dict, Any, List
from datetime import datetime
import jinja2
from .exceptions import ReportGenerationError
from .base import ReportGeneratorInterface


class HTMLReportGenerator(ReportGeneratorInterface):
    """Generates interactive HTML reports with visualizations.

    - Topic timeline visualization
    - Sentiment analysis graphs

    """

    def __init__(self, template_dir: Path):
        """Initialize the HTML report generator"""
        try:
            self.env = jinja2.Environment(
                loader=jinja2.FileSystemLoader(str(template_dir)),
                autoescape=True
            )
        except Exception as e:
            raise ReportGenerationError(f"Failed to initialize template environment: {str(e)}")

    def generate(self, data: Dict[str, Any], output_dir: Path) -> Path:
        """Generate an HTML report synchronously"""
        try:
            if not output_dir.exists():
                output_dir.mkdir(parents=True)

            # Validate required data
            if not data.get('topics') or not data.get('transcription'):
                raise ReportGenerationError("Missing required data fields")

            # Prepare visualization data
            viz_data = self._prepare_visualization_data(data)

            # Render template
            template = self.env.get_template('discussion_analysis.html')
            html = template.render(
                data=data,
                viz_data=viz_data,
                timestamp=datetime.now().isoformat()
            )

            # Write report
            output_file = output_dir / 'analysis_report.html'
            output_file.write_text(html)
            return output_file

        except jinja2.TemplateError as e:
            raise ReportGenerationError(f"Template error: {str(e)}")
        except Exception as e:
            raise ReportGenerationError(f"Failed to generate report: {str(e)}")

    def _prepare_visualization_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data for visualizations"""
        return {
            'timeline': self._create_timeline_data(data['topics']),
            'speakers': self._create_speaker_data(data['transcription']),
            'hierarchy': self._create_hierarchy_data(data),
            'sentiment': self._create_sentiment_data(data)  # Add sentiment data preparation
        }

    def _create_timeline_data(self, topics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create timeline visualization data"""
        return {
            'labels': [t['name'] for t in topics],
            'start': [t['start_time'] for t in topics],
            'end': [t['end_time'] for t in topics]
        }

    def _create_speaker_data(self, transcription: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create speaker statistics visualization data"""
        speakers = {}
        for segment in transcription:
            speaker = segment['speaker_id']
            duration = segment['end_time'] - segment['start_time']
            speakers[speaker] = speakers.get(speaker, 0) + duration
        return {
            'speakers': list(speakers.keys()),
            'durations': list(speakers.values())
        }

    def _create_hierarchy_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create topic hierarchy visualization data"""
        topics = data.get('topics', [])
        return {
            'nodes': [{'id': t['name'], 'value': t.get('importance_score', 1.0)}
                      for t in topics],
            'links': []
        }

    def _create_sentiment_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create sentiment visualization data"""
        # Initialize with default sentiment data if not available
        if 'sentiment' not in data:
            return {
                'overall_sentiment': 0,
                'timeline': [],
                'speaker_sentiments': {}
            }

        sentiment_data = data.get('sentiment', {})
        return {
            'overall_sentiment': sentiment_data.get('overall_sentiment', 0),
            'timeline': [
                {
                    'timestamp': item['timestamp'],
                    'sentiment_score': item['sentiment_score'],
                    'speaker_id': item['speaker_id'],
                    'text': item['text']
                }
                for item in sentiment_data.get('sentiment_timeline', [])
            ],
            'speaker_sentiments': sentiment_data.get('speaker_sentiments', {})
        }