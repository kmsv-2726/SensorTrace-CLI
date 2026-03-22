from rich.console import Console
from rich.panel import Panel
from typing import Optional

console = Console()

def show_logs(filter_str: Optional[str]) -> None:
    """Stub for showing and filtering saved log entries."""
    console.print(Panel.fit(
        f"[bold yellow]Not yet implemented:[/bold yellow] Log viewing\n"
        f"Filter: [cyan]{filter_str if filter_str else 'None'}[/cyan]",
        title="SensorTrace Logs",
        border_style="yellow"
    ))
