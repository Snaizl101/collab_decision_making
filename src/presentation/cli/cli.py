import click
from interfaces import CLIInterface, CLIConfig
from pathlib import Path


class CLI(CLIInterface):

    def __init__(self):
        self.config: CLIConfig = None

        @click.command()
        @click.option('--input-dir', required=True, type=click.Path(exists=True))
        @click.option('--output-dir', required=True, type=click.Path())
        @click.option('--verbose', is_flag=True, help='Enables verbose mode')

    def run(self, input_dir: str, output_dir: str, verbose: bool) -> None:
        click.echo('Collaborative Decision Making System')

        self.config = CLIConfig(Path(input_dir), Path(output_dir), Path(verbose))
        if verbose:
            click.echo(f"Input directory: {input_dir}")
            click.echo(f"Output directory: {output_dir}")

    def handle_input(self, command: str, args: CLIConfig) -> None:
        pass
