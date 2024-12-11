import click
from pathlib import Path
from typing import Optional, Dict, Any, Callable

from presentation.cli.interfaces import UserInterface, OutputFormat
from business.audio.processor import AudioProcessor


class CLI(UserInterface):
    def __init__(self):
        """Initialize CLI with audio processor"""
        self.processor = AudioProcessor()

    def _show_progress(self, status_info: Dict[str, Any]) -> None:
        """Default progress handler"""
        status = status_info['status']
        progress = status_info.get('progress', 0)
        message = status_info.get('message', '')
        click.echo(f"{status}: {progress}% - {message}")

    def start_analysis(self,
                       audio_path: Path,
                       progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> str:
        """Start audio analysis and return session ID"""
        try:
            progress_handler = progress_callback or self._show_progress
            session_id = self.processor.process(audio_path, progress_handler)
            click.echo(f"Started analysis session: {session_id}")
            return session_id
        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
            raise

    def generate_report(self, session_id: str, format: OutputFormat = OutputFormat.HTML) -> Path:
        """Generate and return path to analysis report"""
        try:
            click.echo(f"Generating {format.value} report for session {session_id}")
            report_path = self.processor.generate_report(session_id, format)
            click.echo(f"Report generated: {report_path}")
            return report_path
        except Exception as e:
            click.echo(f"Error: {str(e)}", err=True)
            raise


# CLI Commands setup
@click.group()
@click.pass_context
def cli(ctx):
    """Discussion Analysis System CLI"""
    ctx.obj = CLI()


@cli.command()
@click.argument('audio_path',
                type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option('--verbose', is_flag=True, help='Enable detailed progress output')
@click.pass_context
def analyze(ctx, audio_path: Path, verbose: bool):
    """Start analysis of an audio file"""
    progress_callback = ctx.obj._show_progress if verbose else None
    ctx.obj.start_analysis(audio_path, progress_callback)


@cli.command()
@click.argument('session_id')
@click.option(
    '--format',
    type=click.Choice([f.value for f in OutputFormat]),
    default=OutputFormat.HTML.value,
    help='Report format'
)
@click.pass_context
def report(ctx, session_id: str, format: str):
    """Generate analysis report"""
    output_format = OutputFormat(format)  # Convert string to enum
    ctx.obj.generate_report(session_id, output_format)


if __name__ == '__main__':
    cli()
