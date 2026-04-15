import json
import psutil
import time
import subprocess
from datetime import datetime

LOG_FILE = "alerts.log"
CPU_THRESHOLD = 80.0
INTERVAL = 5


def get_cpu_temperature() -> str:
    """Lit la température CPU via macmon (Apple Silicon, sans sudo)."""
    try:
        result = subprocess.run(
            ["macmon", "pipe", "-s", "1", "-i", "200"],
            capture_output=True, text=True, timeout=3
        )
        data = json.loads(result.stdout.strip().splitlines()[0])
        return f"{data['temp']['cpu_temp_avg']:.1f}°C"
    except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError, KeyError, IndexError):
        pass
    return "N/A"


def send_notification(title: str, message: str) -> None:
    script = f'display notification "{message}" with title "{title}"'
    subprocess.run(["osascript", "-e", script], check=False)


def log_alert(cpu_percent: float, temp: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] ALERTE CPU : {cpu_percent:.1f}% | Temp : {temp} (seuil : {CPU_THRESHOLD}%)\n"
    with open(LOG_FILE, "a") as f:
        f.write(line)
    send_notification("SysDash — Alerte CPU", f"CPU à {cpu_percent:.1f}% — {temp} (seuil {CPU_THRESHOLD}%)")


def monitor() -> None:
    print(f"Surveillance démarrée (intervalle : {INTERVAL}s, seuil CPU : {CPU_THRESHOLD}%)")
    print("-" * 60)
    try:
        while True:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            temp = get_cpu_temperature()

            timestamp = datetime.now().strftime("%H:%M:%S")
            print(
                f"[{timestamp}]  CPU : {cpu:5.1f}%  |  "
                f"RAM : {ram.percent:5.1f}%  "
                f"({ram.used / 1024**3:.1f} Go / {ram.total / 1024**3:.1f} Go)  |  "
                f"Temp : {temp}"
            )

            if cpu > CPU_THRESHOLD:
                log_alert(cpu, temp)
                print(f"           ⚠  Alerte enregistrée dans {LOG_FILE}")

            time.sleep(INTERVAL - 1)  # interval=1 already consumed above
    except KeyboardInterrupt:
        print("\nSurveillance arrêtée.")


if __name__ == "__main__":
    monitor()
