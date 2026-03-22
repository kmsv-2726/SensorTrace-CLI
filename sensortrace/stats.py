from rich.console import Console
from rich.panel import Panel

console = Console()

def display_stats() -> None:
    """Stub for displaying aggregated sensor statistics."""
    console.print(Panel.fit(
        f"[bold yellow]Not yet implemented:[/bold yellow] Sensor statistics aggregation",
        title="SensorTrace Stats",
        border_style="yellow"
    ))
