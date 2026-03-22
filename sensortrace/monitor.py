import time
import psutil
import platform
import subprocess
import sys
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from sensortrace.config import SENSOR_PATHS, SENSOR_PROCESS_NAMES

console = Console()

def check_sensor_apis():
    """Detect hardware sensors using standard psutil endpoints, WMI, and specialized CLI tools."""
    sensors = []
    
    # 1. psutil defaults
    try:
        if hasattr(psutil, "sensors_temperatures"):
            temps = psutil.sensors_temperatures()
            if temps:
                sensors.append("Temperatures (Available)")
    except (AttributeError, NotImplementedError, Exception):
        pass
        
    try:
        if hasattr(psutil, "sensors_fans"):
            fans = psutil.sensors_fans()
            if fans:
                sensors.append("Fans (Available)")
    except (AttributeError, NotImplementedError, Exception):
        pass
        
    try:
        if hasattr(psutil, "sensors_battery"):
            battery = psutil.sensors_battery()
            if battery is not None:
                sensors.append(f"Battery ({int(battery.percent)}%)")
    except (AttributeError, NotImplementedError, Exception):
        pass
        
    # Windows-specific deep probes
    if platform.system() == "Windows":
        # WMI Battery
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-WmiObject -Class Win32_Battery"],
                capture_output=True, text=True, timeout=2
            )
            if result.stdout.strip():
                if "WMI Battery" not in sensors:
                    sensors.append("WMI Battery (Available)")
        except Exception:
            pass

        # NVIDIA GPU
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=temperature.gpu,clocks.current.graphics,power.draw", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(',')
                if parts:
                    temp = parts[0].strip()
                    sensors.append(f"NVIDIA GPU \u2014 {temp}\u00b0C")
        except Exception:
            # Fallback to pynvml
            try:
                import pynvml
                pynvml.nvmlInit()
                handle = pynvml.nvmlDeviceGetHandleByIndex(0)
                temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                sensors.append(f"NVIDIA GPU \u2014 {temp}\u00b0C")
            except Exception:
                pass
                
        # Intel CPU Thermals (WMI ACPI)
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-WmiObject -Namespace root/WMI -Class MSAcpi_ThermalZoneTemperature | Select-Object -ExpandProperty CurrentTemperature"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split('\n')
                if lines:
                    raw_val = int(lines[0].strip())
                    celsius = (raw_val / 10.0) - 273.15
                    sensors.append(f"Intel Thermal ACPI \u2014 {celsius:.1f}\u00b0C")
        except Exception:
            pass

        # ASUS ROG / Hardware EC & Realtek Audio process checks
        has_asus = False
        has_realtek = False
        asus_processes = {"ROGLiveService.exe", "ASUS_FRQ_Control.exe", "ArmouryCrate.Service.exe", "AsusSystemAnalysis.exe"}
        
        try:
            for p in psutil.process_iter(['name']):
                name = p.info.get('name')
                if not name:
                    continue
                if name in asus_processes:
                    has_asus = True
                elif name == "RtkAudUService64.exe":
                    has_realtek = True
                    
                if has_asus and has_realtek:
                    break
        except Exception:
            pass
            
        if has_asus:
            sensors.append("ASUS ROG EC (ArmouryCrate) \u2014 Active")
            
        if has_realtek:
            sensors.append("Realtek Audio HW \u2014 Active")
            
        # Windows Thermal Management
        try:
            result = subprocess.run(
                ["powershell", "-Command", "Get-WmiObject -Class Win32_TemperatureProbe"],
                capture_output=True, text=True, timeout=2
            )
            if result.returncode == 0 and result.stdout.strip():
                sensors.append("Windows Thermal (WMI) \u2014 Available")
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

def generate_dashboard(processes_data, available_apis, stats, interval):
    # Header
    header = Table.grid(expand=True)
    header.add_column(justify="left")
    header.add_column(justify="center")
    header.add_column(justify="right")
    
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    api_str = ", ".join(available_apis) if available_apis else "None detected"
    header.add_row(
        "[bold cyan]SensorTrace Live Monitor[/bold cyan]",
        f"APIs Active: {api_str}",
        f"{current_time} | Refresh: {interval}s"
    )

    # Main Table
    table = Table(
        show_header=True, 
        header_style="bold magenta", 
        expand=True,
        border_style="dim"
    )
    table.add_column("PID", style="dim", justify="right")
    table.add_column("Process Name")
    table.add_column("CPU %", justify="right")
    table.add_column("Mem %", justify="right")
    table.add_column("Sensor Access", justify="center")
    table.add_column("Sensor Path")

    # Limit to current terminal height to prevent the Live layout from cropping weirdly
    max_rows = max(10, console.size.height - 11)
    
    for p in processes_data[:max_rows]:
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
        
    # Footer
    footer = Text(
        f"Processes Scanned: {stats['total']} | Sensor-Accessing: {stats['accessing']} | "
        f"Press Ctrl+C to exit.",
        style="dim",
        justify="center"
    )
    
    # Assembly
    layout = Layout()
    layout.split(
        Layout(Panel(header, style="white"), name="header", size=3),
        Layout(table, name="main"),
        Layout(footer, name="footer", size=1)
    )
    
    return layout

def run_monitor(interval: int, output: str, filter: str, log: bool):
    """Live updating process monitor dashboard."""
    
    available_apis = check_sensor_apis()
    
    # Pass 1: Initialize CPU metrics for all processes.
    # We use interval=None pre-call so it's non-blocking, and successive calls give the actual delta.
    for proc in psutil.process_iter():
        try:
            proc.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    try:
        # Interactive Live view terminal hook
        with Live(console=console, screen=True, refresh_per_second=1) as live:
            while True:
                processes_data = []
                total_scanned = 0
                total_accessing = 0
                
                for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                    total_scanned += 1
                    try:
                        name = proc.info.get('name') or "Unknown"
                        pid = proc.info.get('pid') or 0
                        
                        # Custom filter logic
                        if filter and filter.lower() != "sensor":
                            if filter.lower() not in name.lower():
                                continue

                        cpu = proc.cpu_percent(interval=None)
                        mem = proc.info.get('memory_percent') or 0.0
                        
                        open_files = []
                        try:
                            open_files = proc.open_files()
                        except (psutil.AccessDenied, psutil.NoSuchProcess):
                            pass
                            
                        accessed_sensor_paths = check_sensor_access(open_files)
                        
                        # Windows fallback heuristic
                        if not accessed_sensor_paths and platform.system() == "Windows":
                            if name in SENSOR_PROCESS_NAMES:
                                accessed_sensor_paths = ["WMI/Driver (inferred)"]
                                
                        has_access = "Yes" if accessed_sensor_paths else "No"
                        
                        if has_access == "Yes":
                            total_accessing += 1
                            
                        # `--filter sensor` specifically enforces sensor_access == "Yes"
                        if filter and filter.lower() == "sensor" and has_access == "No":
                            continue
                        
                        processes_data.append({
                            "pid": str(pid),
                            "name": name,
                            "cpu": float(cpu),
                            "mem": float(mem),
                            "has_access": has_access,
                            "paths": "\n".join(accessed_sensor_paths) if accessed_sensor_paths else "None"
                        })
                        
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue

                # Sorting logic
                processes_data.sort(key=lambda x: (x["has_access"] == "No", -x["cpu"]))
                
                stats = {"total": total_scanned, "accessing": total_accessing}
                
                dashboard = generate_dashboard(processes_data, available_apis, stats, interval)
                live.update(dashboard)
                
                # Sleep cycle dictating refresh speed
                time.sleep(interval)
                
    except KeyboardInterrupt:
        console.print("[bold green]Monitoring stopped.[/bold green]")
        sys.exit(0)
