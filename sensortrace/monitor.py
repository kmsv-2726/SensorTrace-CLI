from rich.console import Console
from rich.panel import Panel

console = Console()

def start_monitor(interval: int, output: str) -> None:
    """Stub for starting real-time process and sensor monitoring."""
    console.print(Panel.fit(
        f"[bold yellow]Not yet implemented:[/bold yellow] Real-time monitoring\n"
        f"Interval: [cyan]{interval}s[/cyan]\n"
        f"Output format: [cyan]{output}[/cyan]",
        title="SensorTrace Monitor",
        border_style="yellow"
    ))
