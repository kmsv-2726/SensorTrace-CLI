# SensorTrace CLI

An open-source Python tool for detecting hardware sensor side-channel attacks, designed for security researchers and developers.

## 🚀 Overview

SensorTrace monitors process behavior and hardware sensor access in real-time. It maps process handles, registry flags, and WMI providers to physical hardware sensors to help identify unauthorized sensor polling or potential side-channel leaks.

## ✨ Features

- **Real-Time Live Monitor**: A high-performance `top`-style interactive dashboard powered by Rich.
- **Unified Sensor Engine**:
    - **UWP/Win32 Capabilities**: Detects active usage of Webcams, Microphones, Location, Bluetooth, Activity (step counters), and Gaze tracking via the Windows Registration Store.
    - **App Attribution**: Intelligently identifies specifically which application (e.g., `chrome.exe`, `teams.exe`) is utilizing a hardware capability.
    - **Hardware Thermals**: Real-time polling of NVIDIA GPU (temp/clock), Intel CPU (WMI ACPI), and Windows Temperature Probes.
    - **Battery Snapshot**: Detailed charge levels and power consumption tracking.
    - **Vendor Support**: Integrated detection for ASUS ROG EC (Armoury Crate) and Realtek Audio hardware.
- **Optimized Polling**: High-speed, non-recursive registry and CIM polling ensures a sub-second UI refresh even on systems with hundreds of processes.
- **Priority Detection**: Automatically floats and highlights processes with active sensor access to the top of the monitor.
- **Filtering**: Isolate specific apps or view *only* active sensor-accessing processes with `--filter sensor`.

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

# High-priority mode: only show processes with sensor access
poetry run sensortrace monitor --filter sensor --interval 1

# Filter for a specific process keyword
poetry run sensortrace monitor --filter "Teams"
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
- **WMI/CIM/PowerShell**: Deep Windows hardware and registry integration

## 🛡 Disclaimer
*On Windows, UWP and desktop app sensor access is detected via CapabilityAccessManager registry flags. For deep file handle inspection, running the terminal as Administrator is recommended.*
