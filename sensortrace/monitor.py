import time
import psutil
import platform
import subprocess
import sys
import json
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from sensortrace.config import SENSOR_PATHS, SENSOR_PROCESS_NAMES

console = Console()

UWP_SENSORS = [
    "webcam", 
    "microphone", 
    "location", 
    "bluetooth", 
    "activity", 
    "gazeInput"
]

API_TYPE_MAPPING = {
    "WmiPrvSE.exe": "WMI Thermal",
    "nvcontainer.exe": "NVIDIA GPU",
    "nvsphelper64.exe": "NVIDIA GPU",
    "MsMpEng.exe": "WMI Defender",
    "PhoneExperienceHost.exe": "UWP Proximity",
}

def get_api_type(process_name: str) -> str:
    return API_TYPE_MAPPING.get(process_name, "WMI/Driver")

def check_all_sensors_windows() -> list:
    """Consolidated Windows hardware and UWP sensor check via optimized PowerShell polling."""
    sensors = []
    
    # Avoid slow -Recurse. Traverse UWP packages and NonPackaged subkeys targetfully.
    script = r"""
$ErrorActionPreference = 'SilentlyContinue'
$results = @()
$uwpTypes = @('webcam', 'microphone', 'location', 'bluetooth', 'activity', 'gazeInput')

foreach ($t in $uwpTypes) {
    $path = "HKCU:\Software\Microsoft\Windows\CurrentVersion\CapabilityAccessManager\ConsentStore\$t"
    if (Test-Path $path) {
        $entry = @{name=$t; type='uwp'; available=$true; active=$false; app=""}
        $items = Get-ChildItem $path
        foreach ($item in $items) {
            if ($item.PSChildName -eq 'NonPackaged') {
                $win32Apps = Get-ChildItem $item.PSPath
                foreach ($app in $win32Apps) {
                    $p = Get-ItemProperty $app.PSPath
                    if ($p.LastUsedTimeStart -and $p.LastUsedTimeStart -ne 0 -and ($null -eq $p.LastUsedTimeStop -or $p.LastUsedTimeStop -eq 0)) {
                        $entry.active = $true
                        $entry.app = $app.PSChildName.Replace('#', '\')
                        break
                    }
                }
            } else {
                $p = Get-ItemProperty $item.PSPath
                if ($p.LastUsedTimeStart -and $p.LastUsedTimeStart -ne 0 -and ($null -eq $p.LastUsedTimeStop -or $p.LastUsedTimeStop -eq 0)) {
                    $entry.active = $true
                    $entry.app = $item.PSChildName
                    break
                }
            }
            if ($entry.active) { break }
        }
        $results += $entry
    }
}

# CIM is usually faster than WMI for hardware probes
$intel = Get-CimInstance -Namespace root/WMI -ClassName MSAcpi_ThermalZoneTemperature | Select-Object -First 1
if ($intel) {
    $celsius = ($intel.CurrentTemperature / 10.0) - 273.15
    $results += @{name='Intel Thermal'; type='hardware'; available=$true; active=$false; value=([string]::Format("{0:N1}°C", $celsius))}
}

$battery = Get-CimInstance -ClassName Win32_Battery | Select-Object -First 1
if ($battery) {
    $results += @{name='WMI Battery'; type='hardware'; available=$true; active=$false; value='Available'}
}

$results | ConvertTo-Json -Compress
"""
    try:
        ps_result = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            capture_output=True, text=True, timeout=5
        )
        if ps_result.returncode == 0 and ps_result.stdout.strip():
            # If only 1 object is returned, JSON may not be an array
            data = json.loads(ps_result.stdout.strip())
            if isinstance(data, dict):
                sensors.append(data)
            else:
                sensors.extend(data)
    except Exception:
        pass

    # NVIDIA Snapshot (Native CLI)
    try:
        nv_result = subprocess.run(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=2
        )
        if nv_result.returncode == 0 and nv_result.stdout.strip():
            sensors.append({
                "name": "NVIDIA GPU",
                "type": "hardware",
                "available": True,
                "active": False,
                "value": f"{nv_result.stdout.strip()}°C"
            })
    except Exception:
        pass

    # Standard psutil battery
    try:
        bat = psutil.sensors_battery()
        if bat:
            sensors.append({
                "name": "Battery",
                "type": "hardware",
                "available": True,
                "active": False,
                "value": f"{int(bat.percent)}%"
            })
    except Exception:
        pass

    # ASUS ROG EC process check
    asus_procs = {"ROGLiveService.exe", "ArmouryCrate.Service.exe", "ASUS_FRQ_Control.exe", "AsusSystemAnalysis.exe"}
    try:
        found_asus = False
        for p in psutil.process_iter(['name']):
            if p.info['name'] in asus_procs:
                found_asus = True
                break
        if found_asus:
            sensors.append({"name": "ASUS ROG EC", "type": "hardware", "available": True, "active": False, "value": "Active"})
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
    active_apis = [api for api in available_apis if api.get("active")]
    idle_apis = [api for api in available_apis if not api.get("active")]

    # Active Header parts - Fix case and display
    active_parts = []
    for api in active_apis:
        clean_name = api['name'].capitalize()
        app_display = api.get('app', '')
        if "\\" in app_display:
            app_display = app_display.split("\\")[-1]
        
        if app_display:
            active_parts.append(f"{clean_name} ({app_display})")
        else:
            active_parts.append(f"{clean_name}")
    active_str = ", ".join(active_parts) if active_parts else "None detected"

    # Idle Header parts
    idle_parts = []
    for api in idle_apis:
        val = api.get('value', 'Available')
        idle_parts.append(f"{api['name']} ({val})")
    idle_str = ", ".join(idle_parts) if idle_parts else "None detected"

    # Layout construction
    header = Table.grid(expand=True)
    header.add_column(justify="left")
    header.add_column(justify="center")
    header.add_column(justify="right")
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header.add_row(
        "[bold cyan]SensorTrace Live Monitor[/bold cyan]",
        f"[bold bright_green]APIs Active:[/bold bright_green] {active_str}",
        f"{current_time} | Refresh: {interval}s"
    )

    header2 = Table.grid(expand=True)
    header2.add_column(justify="left")
    header2.add_column(justify="center")
    header2.add_column(justify="right")
    header2.add_row(
        "", f"[bold dim]APIs Idle:[/bold dim] {idle_str}", ""
    )

    table = Table(show_header=True, header_style="bold magenta", expand=True, border_style="dim")
    table.add_column("PID", style="dim", justify="right")
    table.add_column("Process Name")
    table.add_column("API Type", justify="center")
    table.add_column("CPU %", justify="right")
    table.add_column("Mem %", justify="right")
    table.add_column("Sensor Access", justify="center")
    table.add_column("Sensor Path")

    max_rows = max(10, console.size.height - 13)
    for p in processes_data[:max_rows]:
        style = "yellow" if p["has_access"] == "Yes" else ""
        table.add_row(
            p["pid"], p["name"], p["api_type"], f"{p['cpu']:.1f}", f"{p['mem']:.1f}",
            p["has_access"], p["paths"], style=style
        )
        
    footer = Text(
        f"Processes Scanned: {stats['total']} | Sensor-Accessing: {stats['accessing']} | Press Ctrl+C to exit.",
        style="dim", justify="center"
    )
    
    layout = Layout()
    layout.split(
        Layout(Panel(header, style="white"), name="header", size=3),
        Layout(Panel(header2, style="white"), name="header2", size=3),
        Layout(table, name="main"),
        Layout(footer, name="footer", size=1)
    )
    return layout

def run_monitor(interval: int, output: str, filter: str, log: bool):
    """Live updating process monitor dashboard featuring consolidated Windows sensor polling."""
    # Init CPU
    for proc in psutil.process_iter():
        try:
            proc.cpu_percent(interval=None)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    try:
        with Live(console=console, screen=True, refresh_per_second=1) as live:
            while True:
                # 1. Fetch current sensor state (consolidated and faster)
                sensors = check_all_sensors_windows() if platform.system() == "Windows" else []
                active_uwp_apps = {} # map app_name to sensor_type
                for s in sensors:
                    if s.get('active') and s.get('app'):
                        # app might be whole path
                        app_name = s['app'].split("\\")[-1].lower()
                        active_uwp_apps[app_name] = s['name'].capitalize()

                processes_data = []
                total_scanned = 0
                total_accessing = 0
                
                # 2. Iter processes
                for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
                    total_scanned += 1
                    try:
                        name = proc.info.get('name') or "Unknown"
                        pid = proc.info.get('pid') or 0
                        
                        if filter and filter.lower() != "sensor":
                            if filter.lower() not in name.lower():
                                continue

                        cpu = proc.cpu_percent(interval=None)
                        mem = proc.info.get('memory_percent') or 0.0
                        
                        # Check access sources
                        paths = []
                        try:
                            paths = check_sensor_access(proc.open_files())
                        except (psutil.AccessDenied, psutil.NoSuchProcess):
                            pass
                            
                        # API Type mapping
                        api_type = ""
                        # Priority 1: UWP sensor detected via registry
                        if name.lower() in active_uwp_apps:
                            api_type = f"UWP {active_uwp_apps[name.lower()]}"
                            if not paths:
                                paths = ["Registry Flag (Active)"]
                        
                        # Priority 2: Traditional SENSOR_PROCESS_NAMES
                        if not api_type and name in SENSOR_PROCESS_NAMES:
                            api_type = get_api_type(name)
                            if not paths:
                                paths = ["WMI/Driver (inferred)"]

                        has_access = "Yes" if paths else "No"
                        if has_access == "Yes":
                            total_accessing += 1
                            if not api_type:
                                api_type = "WMI/Driver"
                        
                        if filter and filter.lower() == "sensor" and has_access == "No":
                            continue
                        
                        processes_data.append({
                            "pid": str(pid), "name": name, "api_type": api_type,
                            "cpu": float(cpu), "mem": float(mem), "has_access": has_access,
                            "paths": "\n".join(paths) if paths else "None"
                        })
                        
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        continue

                # Sorting - show sensor-accessing processes (including active UWP apps) at the top
                processes_data.sort(key=lambda x: (x["has_access"] == "No", -x["cpu"]))
                
                stats = {"total": total_scanned, "accessing": total_accessing}
                dashboard = generate_dashboard(processes_data, sensors, stats, interval)
                live.update(dashboard)
                time.sleep(interval)
                
    except KeyboardInterrupt:
        console.print("[bold green]Monitoring stopped.[/bold green]")
        sys.exit(0)