import time
import psutil
import platform
import subprocess
from rich.console import Console
from rich.table import Table
from sensortrace.config import SENSOR_PATHS, SENSOR_PROCESS_NAMES

console = Console()

def check_sensor_apis():
    """Detect hardware sensors using standard psutil endpoints and WMI."""
    sensors = []
    
    try:
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                sensors.append("Temperatures")
    except (AttributeError, NotImplementedError, Exception):
        pass
        
    try:
        if hasattr(psutil, "sensors_fans"):
            fans = psutil.sensors_fans()
            if fans:
                sensors.append("Fans")
    except (AttributeError, NotImplementedError, Exception):
        pass
        
    try:
        if hasattr(psutil, "sensors_battery"):
            battery = psutil.sensors_battery()
            if battery is not None:
                sensors.append("Battery")
    except (AttributeError, NotImplementedError, Exception):
        pass
        
    # Windows-specific WMI check for battery
    if platform.system() == "Windows":
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-WmiObject -Class Win32_Battery"],
                capture_output=True, text=True, timeout=2
            )
            if result.stdout.strip():
                if "WMI Battery" not in sensors:
                    sensors.append("WMI Battery")
        except Exception:
            pass
            
    return sensors

def check_sensor_access(proc_open_files):
    """Compare a process's open file list against known sensor endpoints."""
    accessed_paths = []
    if not proc_open_files:
        return accessed_paths
        
    for file in proc_open_files:
        path = file.path
        for sensor_path in SENSOR_PATHS:
            if sensor_path.lower() in path.lower():
                accessed_paths.append(path)
                
    return accessed_paths

def run_monitor(interval: int, output: str, filter: str, log: bool):
    """Single snapshot of all running processes and their sensor access status."""
    
    if output.lower() != "table":
        console.print(f"[yellow]\u26a0 Output format '{output}' not yet implemented. Falling back to 'table'.[/yellow]")

    if log:
        console.print("[yellow]\u26a0 File logging is currently disabled (coming Week 3).[/yellow]")

    # Check for hardware support from psutil and WMI
    available_apis = check_sensor_apis()
    if available_apis:
        console.print(f"[bold cyan]Available System Sensor APIs:[/bold cyan] {', '.join(available_apis)}")
    else:
        console.print("[yellow]Warnings: No standard hardware sensor APIs detected.[/yellow]")

    table = Table(title="SensorTrace - Process Monitor (Single Snapshot)", show_header=True, header_style="bold magenta")
    table.add_column("PID", style="dim", justify="right")
    table.add_column("Process Name")
    table.add_column("CPU %", justify="right")
    table.add_column("Mem %", justify="right")
    table.add_column("Sensor Access", justify="center")
    table.add_column("Sensor Path")

    # Pass 1: Initialize CPU metrics for all processes so cpu_percent returns meaningful data > 0.0
    for proc in psutil.process_iter():
        try:
            proc.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    # Short sleep interval so the CPU usage delta is actually captured
    time.sleep(0.1)

    processes_data = []
    
    # Pass 2: Actually collect snapshot data
    for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
        try:
            name = proc.info.get('name') or "Unknown"
            pid = proc.info.get('pid') or 0
            
            # Apply filter early if specified via `--filter` flag
            if filter and filter.lower() not in name.lower():
                continue

            cpu = proc.cpu_percent(interval=None)
            mem = proc.info.get('memory_percent') or 0.0
            
            open_files = []
            try:
                # `open_files()` fails if we don't have adequate ACL permissions/root
                open_files = proc.open_files()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
                
            accessed_sensor_paths = check_sensor_access(open_files)
            
            # Windows fallback heuristic
            if not accessed_sensor_paths and platform.system() == "Windows":
                # Exact match against the SENSOR_PROCESS_NAMES list
                if name in SENSOR_PROCESS_NAMES:
                    accessed_sensor_paths = ["WMI/Driver (inferred)"]
            
            processes_data.append({
                "pid": str(pid),
                "name": name,
                "cpu": float(cpu),
                "mem": float(mem),
                "has_access": "Yes" if accessed_sensor_paths else "No",
                "paths": "\n".join(accessed_sensor_paths) if accessed_sensor_paths else "None"
            })
            
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    # Sorting: Sensor access Yes first, then by highest CPU percentage utilization
    processes_data.sort(key=lambda x: (x["has_access"] == "No", -x["cpu"]))
    
    # Display ALL results (no truncation)
    for p in processes_data:
        style = "yellow" if p["has_access"] == "Yes" else ""
        table.add_row(
            p["pid"],
            p["name"],
            f"{p['cpu']:.1f}",
            f"{p['mem']:.1f}",
            p["has_access"],
            p["paths"],
            style=style
        )
        
    console.print(table)
    
    # Final info footer
    footer_text = "* Sensor access detection uses WMI provider identification and direct file handle inspection. Specificity prioritized over recall — only known sensor processes are flagged."
    console.print(f"\n[dim]{footer_text}[/dim]")
