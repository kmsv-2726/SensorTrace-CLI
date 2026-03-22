import typer
from typing import Optional
from sensortrace.monitor import run_monitor
from sensortrace.logger import show_logs
from sensortrace.stats import show_stats

app = typer.Typer(
    name="sensortrace",
    help="SensorTrace CLI \u2014 A tool for detecting hardware sensor side-channel attacks.",
    no_args_is_help=True
)

@app.command()
def monitor(
    interval: int = typer.Option(1, "--interval", help="Monitoring refresh interval in seconds."),
    output: str = typer.Option("table", "--output", help="Output format (e.g., table, json)."),
    filter: Optional[str] = typer.Option(None, "--filter", help="Filter by process name, or use 'sensor' for only active processes."),
    log: bool = typer.Option(False, "--log", help="Enable logging of sensor data.")
):
    """
    Start real-time process and sensor monitoring dashboard.
    """
    run_monitor(interval=interval, output=output, filter=filter, log=log)


@app.command()
def logs(
    file: Optional[str] = typer.Option(None, "--file", help="Path to specific log file."),
    filter: Optional[str] = typer.Option(None, "--filter", help="Filter logs by keyword."),
    since: Optional[int] = typer.Option(None, "--since", help="Show logs since X minutes ago.")
):
    """
    Show and filter saved log entries.
    """
    show_logs(file=file, filter=filter, since=since)


@app.command()
def stats(
    export: Optional[str] = typer.Option("csv", "--export", help="Format to export statistics.")
):
    """
    Display aggregated sensor statistics.
    """
    show_stats(export=export)


def main():
    app()

if __name__ == "__main__":
    main()
