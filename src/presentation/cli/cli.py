import click
from pathlib import Path
import asyncio
from typing import Optional, Dict, Any, Callable
import logging
import warnings
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TimeElapsedColumn, TextColumn, BarColumn
from rich.logging import RichHandler

from src.settings import Settings
from src.presentation.cli.base import UserInterface
from src.business.pipeline import Pipeline
from src.business.audio.processors import CombinedProcessor
from src.business.analysis.topic.analyzer import TopicAnalyzer
from src.business.analysis.sentiment.analyzer import SentimentAnalyzer
from business.analysis.llm_client import TogetherLLMClient
from src.storage.dao.sqlite.sqlite_dao import SQLiteDAO
from src.storage.files.local_storage import LocalFileStorage
from src.presentation.reports.generators import HTMLReportGenerator
from src.custom_types import OutputFormat, ProcessingStatus
from dotenv import load_dotenv

project_root = Path(__file__).parent.parent.parent.parent
load_dotenv(project_root / ".env")


class CLI(UserInterface):
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize CLI with complete pipeline and settings"""
        # Set up enhanced logging with Rich
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            handlers=[RichHandler(rich_tracebacks=True)]
        )

        # Initialize Rich console
        self.console = Console()

        # Store config_path as instance variable
        self.config_path = config_path or Path("config/config.yaml")
        # Load settings
        self.settings = Settings(self.config_path)  # Use the stored config path

        # Filter known warnings
        warnings.filterwarnings("ignore", category=UserWarning, module="whisper")
        warnings.filterwarnings("ignore", category=UserWarning, module="pyannote.audio")
        warnings.filterwarnings("ignore", category=FutureWarning, module="torch")

        # Load settings
        self.settings = Settings(config_path or Path("config/config.yaml"))

        # Initialize components with error handling
        try:
            self._initialize_components()
        except Exception as e:
            self.console.print(f"[red]Failed to initialize components: {str(e)}")
            raise

    def _initialize_components(self):
        """Initialize all pipeline components with settings"""
        self.audio_processor = CombinedProcessor(
            stable_model_size="base",
            auth_token="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"
        )

        self.dao = SQLiteDAO(self.settings.db_path)

        self.file_storage = LocalFileStorage(
            Path(self.settings.config['storage']['file_storage_path'])
        )

        self.llm_client = TogetherLLMClient(config_path=self.config_path)

        self.topic_analyzer = TopicAnalyzer(self.llm_client)

        self.sentiment_analyzer = SentimentAnalyzer(self.llm_client)

        self.report_generator = HTMLReportGenerator(
            Path("src/presentation/reports/templates")
        )

        self.pipeline = Pipeline(
            audio_processor=self.audio_processor,
            dao=self.dao,
            file_storage=self.file_storage,
            topic_analyzer=self.topic_analyzer,
            sentiment_analyzer=self.sentiment_analyzer,
            report_generator=self.report_generator
        )

    def _show_progress(self, status_info: Dict[str, Any]) -> None:
        """Enhanced progress handler with Rich progress bars"""
        status: ProcessingStatus = status_info['status']
        progress: float = status_info.get('progress', 0)
        message: str = status_info.get('message', '')

        if status == ProcessingStatus.FAILED:
            self.console.print(f"[red]Error: {message}[/red]")
        elif status == ProcessingStatus.COMPLETED:
            self.console.print(f"[green]Complete: {message}[/green]")
        else:
            with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TimeElapsedColumn(),
                    console=self.console,
                    transient=True
            ) as progress:
                task = progress.add_task(f"[cyan]{status.value}: {message}", total=100)
                progress.update(task, completed=progress * 100)

    async def _run_pipeline(self, audio_path: Path) -> Path:
        """Run the pipeline with progress tracking"""
        with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=self.console
        ) as progress:
            main_task = progress.add_task("[cyan]Processing...", total=100)

            try:
                report_path = await self.pipeline.process(audio_path)
                progress.update(main_task, completed=100, description="[green]Complete!")
                return report_path
            except Exception as e:
                progress.update(main_task, description=f"[red]Error: {str(e)}")
                raise

    def start_analysis(self, audio_path: Path,
                       progress_callback: Callable[[Dict[str, Any]], None]) -> str:
        """Start audio analysis with enhanced error handling"""
        try:
            report_path = asyncio.run(self._run_pipeline(audio_path))
            self.console.print(f"[green]Analysis complete![/green]")
            self.console.print(f"Report generated at: {report_path}")
            return str(report_path)
        except Exception as e:
            self.console.print(f"[red]Error during analysis: {str(e)}[/red]")
            raise

    def generate_report(self, session_id: str, output_dir: Path,
                        format: OutputFormat = OutputFormat.HTML) -> Path:
        """Generate report with progress tracking"""
        try:
            with self.console.status("[cyan]Generating report..."):
                discussion_data = self.dao.get_discussion_summary(session_id)
                report_path = asyncio.run(self.report_generator.generate(
                    discussion_data,
                    output_dir
                ))
            return report_path
        except Exception as e:
            self.console.print(f"[red]Error generating report: {str(e)}[/red]")
            raise


@click.group()
def cli():
    """Discussion Analysis System CLI"""
    pass


@cli.command()
@click.argument('audio_file',
                type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option('--output-dir',
              type=click.Path(file_okay=False, path_type=Path),
              default=Path("output"),
              help='Directory for output files')
@click.option('--config',
              type=click.Path(exists=True, dir_okay=False, path_type=Path),
              default=None,
              help='Path to config file')
def analyze(audio_file: Path, output_dir: Path, config: Optional[Path]):
    """Analyze an audio file and generate a report"""
    console = Console()
    console.print(f"[cyan]Starting analysis of: {audio_file}[/cyan]")

    try:
        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        # Create CLI instance with config
        cli_instance = CLI(config_path=config)

        report_path = cli_instance.start_analysis(
            audio_file,
            progress_callback=cli_instance._show_progress
        )

        console.print("[green]Analysis completed successfully! ✨[/green]")
        console.print(f"You can find the report at: [blue]{report_path}[/blue]")

    except Exception as e:
        console.print(f"[red]Analysis failed: {str(e)}[/red]")
        raise click.Abort()


if __name__ == '__main__':
    cli()
