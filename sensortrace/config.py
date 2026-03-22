SENSOR_PATHS = [
    # General & Linux paths
    "/dev/cpu", 
    "/sys/class/hwmon", 
    "/sys/class/thermal",
    "/sys/class/power_supply",
    "/proc/acpi", 
    "/dev/mem", 
    "/dev/port",
    
    # Windows paths
    "\\\\Device\\\\PhysicalMemory",
    "\\\\Device\\\\Battery",
    "\\\\Device\\\\ACPI",
    "ROOT\\\\ACPI_HAL",
    
    # macOS
    "IOKit",
    "AppleSMC"
]

SENSOR_PROCESS_NAMES = [
    "WmiPrvSE.exe",           # WMI sensor provider (specific)
    "nvcontainer.exe",        # NVIDIA GPU sensor
    "nvsphelper64.exe",       # NVIDIA sensor helper
    "MsMpEng.exe",            # Windows Defender thermal monitor
    "WindowsCamera.exe",      # Camera sensor
    "PhoneExperienceHost.exe",# Proximity/motion sensor host
    "SensorsService.exe",     # Windows Sensor service
    "SensorService.exe",      # alternate spelling
    "ipf_helper.exe",         # Intel sensor helper
    "HWINFO64.exe",           # Hardware monitoring tool
    "HWiNFO64.exe",
    "CPU-Z.exe",
    "GPU-Z.exe",
    "OpenHardwareMonitor.exe",
    "LibreHardwareMonitor.exe",
]

REFRESH_INTERVAL = 1
LOG_DIR = "~/.sensortrace/logs"
APP_NAME = "SensorTrace"
VERSION = "0.1.0"
