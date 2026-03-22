import typer
from typing import Annotated, Optional
from rich.console import Console

from sensortrace.monitor import start_monitor
from sensortrace.logger import show_logs
from sensortrace.stats import display_stats
from sensortrace.config import DEFAULT_INTERVAL

app = typer.Typer(
    name="sensortrace",
    help="SensorTrace CLI \u2014 A tool for detecting hardware sensor side-channel attacks.",
    no_args_is_help=True
)
console = Console()

@app.command()
def monitor(
    interval: Annotated[int, typer.Option("--interval", "-i", help="Monitoring interval in seconds.")] = DEFAULT_INTERVAL,
    output: Annotated[str, typer.Option("--output", "-o", help="Output format (e.g., json, csv).")] = "json"
):
    """
    Start real-time process and sensor monitoring.
    """
    start_monitor(interval=interval, output=output)

@app.command()
def logs(
    filter_word: Annotated[Optional[str], typer.Option("--filter", "-f", help="Filter logs by keyword.")] = None
):
    """
    Show and filter saved log entries.
    """
    show_logs(filter_str=filter_word)

@app.command()
def stats():
    """
    Display aggregated sensor statistics.
    """
    display_stats()

def main():
    app()

if __name__ == "__main__":
    main()
