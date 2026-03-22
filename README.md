# SensorTrace CLI

An open-source Python tool for detecting hardware sensor side-channel attacks, designed for security researchers and developers.

## 🚀 Overview

SensorTrace monitors process behavior and hardware sensor access in real-time, helping identify potential side-channel leaks or unauthorized sensor polling. It uses an intelligent detection engine to map process handles and WMI providers to physical hardware sensors.

## ✨ Features

- **Real-Time Live Monitor**: A `top`-style interactive dashboard powered by Rich.
- **Deep Sensor Probing**:
    - **NVIDIA GPU**: Real-time temperature, clock, and power monitoring via `nvidia-smi`.
    - **Intel CPU**: Thermal zone monitoring via WMI ACPI.
    - **Battery**: Detailed polling of charge levels and discharge rates.
    - **Vendor Specifics**: Support for ASUS ROG EC (Armoury Crate) and Realtek Audio hardware detection.
- **Heuristic Detection Engine**: 
    - Cross-references open file handles against a known database of sensor paths (`/dev/cpu`, `/sys/class/hwmon`, etc.).
    - Windows-specific fallback heuristics to identify WMI provider processes (`WmiPrvSE.exe`, `SensorsService.exe`, etc.).
- **Smart Result Sorting**: Automatically floats processes with active sensor access to the top and highlights them.
- **Filtering**: Ability to isolate specific processes or view *only* sensor-accessing ones with `--filter sensor`.

## 🛠 Installation

This project uses [Poetry](https://python-poetry.org/) for dependency management.

```powershell
# Clone the repository
git clone https://github.com/kmsv-2726/SensorTrace-CLI.git
cd SensorTrace-CLI

# Install dependencies
poetry install
```

## 📖 Usage

### Live Monitoring
The primary command for real-time analysis:
```powershell
# Start the interactive dashboard (1s refresh)
poetry run sensortrace monitor

# Filter for a specific process
poetry run sensortrace monitor --filter "chrome"

# High-priority mode: only show processes with sensor access
poetry run sensortrace monitor --filter sensor --interval 2
```

### Log Viewing (Stubbed)
```powershell
poetry run sensortrace logs --filter "unauthorized"
```

### Statistics (Stubbed)
```powershell
poetry run sensortrace stats --export csv
```

## 🔧 Technical Stack

- **Python 3.10+**
- **Typer**: CLI Framework
- **Rich**: Terminal UI, Layouts, and Live streams
- **psutil**: System and process utilization
- **WMI/PowerShell**: Deep Windows hardware integration

## 🛡 Disclaimer
*On Windows, some sensor access is inferred via WMI provider identification. For deep file handle inspection, running the terminal as Administrator is recommended.*
