SENSOR_PATHS = [
    "/dev/cpu", "/sys/class/hwmon", "/sys/class/thermal",
    "/proc/acpi", "/dev/mem", "/dev/port",
    "\\\\Device\\\\PhysicalMemory",  # Windows
    "IOKit",                         # macOS
]
REFRESH_INTERVAL = 1
LOG_DIR = "~/.sensortrace/logs"
APP_NAME = "SensorTrace"
VERSION = "0.1.0"
