import click
from pathlib import Path
from typing import Optional

from .interfaces import UserInterface
from .business.processor import AudioProcessor


class CLI(UserInterface):
    def __init__(self):
        """Initialize CLI with audio processor"""
        self.processor = AudioProcessor()

    def process_audio(self, input_dir: Path, output_dir: Path, verbose: bool = False) -> None:
        """Process audio files implementation"""
        try:
            if verbose:
                click.echo(f"Processing files from {input_dir}")
                click.echo(f"Output will be saved to {output_dir}")

            self.processor.process(input_dir, output_dir)
        except Exception as e:
            self.display_error(str(e))
            raise

    def generate_report(self, session_id: str, format: str = 'html') -> None:
        """Generate report implementation"""
        try:
            click.echo(f"Generating {format} report for session {session_id}")
            self.processor.generate_report(session_id, format)
            click.echo("Report generated successfully")
        except Exception as e:
            self.display_error(str(e))
            raise

    def show_status(self, session_id: Optional[str] = None) -> None:
        """Show status implementation"""
        try:
            status = self.processor.get_status(session_id)
            click.echo(status)
        except Exception as e:
            self.display_error(str(e))
            raise

    def display_progress(self, message: str, percentage: Optional[float] = None) -> None:
        """Display progress implementation"""
        if percentage is not None:
            click.echo(f"{message}: {percentage:.1f}%")
        else:
            click.echo(message)

    def display_error(self, error: str) -> None:
        """Display error implementation"""
        click.echo(f"Error: {error}", err=True)


# CLI Commands setup
@click.group()
@click.pass_context
def cli(ctx):
    """Discussion Analysis System CLI"""
    ctx.obj = CLI()


@cli.command()
@click.option(
    '--input-dir',
    required=True,
    type=click.Path(exists=True, file_okay=False, dir_okay=True),
    help='Directory containing audio files'
)
@click.option(
    '--output-dir',
    required=True,
    type=click.Path(file_okay=False, dir_okay=True),
    help='Directory for output files'
)
@click.option('--verbose', is_flag=True, help='Enable verbose output')
@click.pass_context
def process(ctx, input_dir: str, output_dir: str, verbose: bool):
    """Process audio files from input directory"""
    ctx.obj.process_audio(Path(input_dir), Path(output_dir), verbose)


@cli.command()
@click.argument('session_id')
@click.option(
    '--format',
    type=click.Choice(['html', 'pdf']),
    default='html',
    help='Report format'
)
@click.pass_context
def report(ctx, session_id: str, format: str):
    """Generate analysis report"""
    ctx.obj.generate_report(session_id, format)


@cli.command()
@click.argument('session_id', required=False)
@click.pass_context
def status(ctx, session_id: Optional[str] = None):
    """Show processing status"""
    ctx.obj.show_status(session_id)


if __name__ == '__main__':
    cli()