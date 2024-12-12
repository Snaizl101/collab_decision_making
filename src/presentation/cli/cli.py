import click
from pathlib import Path
from typing import Optional, Dict, Any, Callable

from presentation.cli.interfaces import UserInterface
from business.audio.processor import AudioProcessor
from custom_types import OutputFormat, ProcessingStatus


class CLI(UserInterface):
    def __init__(self, audio_processor: AudioProcessor):
        """Initialize CLI with audio processor"""
        self.processor = audio_processor

    def _show_progress(self, status_info: Dict[str, Any]) -> None:
        """Progress handler for showing processing status"""
        status: ProcessingStatus = status_info['status']
        progress: float = status_info.get('progress', 0)
        message: str = status_info.get('message', '')

        # Format output based on status
        if status == ProcessingStatus.FAILED:
            click.secho(f"Error: {message}", fg='red', err=True)
        elif status == ProcessingStatus.COMPLETED:
            click.secho(f"Complete: {message}", fg='green')
        else:
            click.echo(f"{status.value}: {progress}% - {message}")

    def start_analysis(self,
                       input_dir: Path,
                       output_dir: Path) -> str:
        """Start audio analysis and return session ID"""
        try:
            # Ensure directories exist
            input_dir.mkdir(parents=True, exist_ok=True)
            output_dir.mkdir(parents=True, exist_ok=True)

            session_id = self.processor.process(
                input_dir=input_dir,
                output_dir=output_dir,
                progress_handler=self._show_progress
            )
            return session_id
        except Exception as e:
            click.secho(f"Error: {str(e)}", fg='red', err=True)
            raise

    def generate_report(self,
                        session_id: str,
                        output_dir: Path,
                        format: OutputFormat = OutputFormat.HTML) -> Path:
        """Generate and return path to analysis report"""
        try:
            click.echo(f"Generating {format.value} report for session {session_id}")
            output_dir.mkdir(parents=True, exist_ok=True)

            report_path = self.processor.generate_report(
                session_id,
                format,
                output_dir=output_dir
            )
            click.secho(f"Report generated: {report_path}", fg='green')
            return report_path
        except Exception as e:
            click.secho(f"Error: {str(e)}", fg='red', err=True)
            raise


@click.group()
def cli():
    """Discussion Analysis System CLI"""
    pass


@cli.command()
@click.option('--input-dir',
              type=click.Path(exists=True, file_okay=False, path_type=Path),
              required=True,
              help='Directory containing input audio files')
@click.option('--output-dir',
              type=click.Path(file_okay=False, path_type=Path),
              required=True,
              help='Directory for output files')
def analyze(input_dir: Path,
            output_dir: Path):
    """Start analysis of audio files in the input directory"""
    audio_processor = AudioProcessor()
    cli_instance = CLI(audio_processor)
    cli_instance.start_analysis(input_dir, output_dir)


@cli.command()
@click.argument('session_id')
@click.option('--output-dir',
              type=click.Path(file_okay=False, path_type=Path),
              required=True,
              help='Directory for report output')
@click.option(
    '--format',
    type=click.Choice([f.value for f in OutputFormat]),
    default=OutputFormat.HTML.value,
    help='Report format'
)
def report(session_id: str,
           output_dir: Path,
           format: str):
    """Generate analysis report"""
    audio_processor = AudioProcessor()
    cli_instance = CLI(audio_processor)
    output_format = OutputFormat(format)  # Convert string to enum
    cli_instance.generate_report(
        session_id,
        output_dir,
        output_format
    )


if __name__ == '__main__':
    cli()