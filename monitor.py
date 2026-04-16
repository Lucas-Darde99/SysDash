import json
import psutil
import time
import shutil
import subprocess
from datetime import datetime, timedelta

LOG_FILE = "alerts.log"
CPU_THRESHOLD = 80.0
INTERVAL = 5

WIDTH = 62


def get_cpu_temperature() -> str:
    try:
        result = subprocess.run(
            ["macmon", "pipe", "-s", "1", "-i", "200"],
            capture_output=True, text=True, timeout=3
        )
        data = json.loads(result.stdout.strip().splitlines()[0])
        return f"{data['temp']['cpu_temp_avg']:.1f}°C"
    except (subprocess.TimeoutExpired, FileNotFoundError,
            json.JSONDecodeError, KeyError, IndexError):
        pass
    return "N/A"


def get_uptime() -> str:
    boot = datetime.fromtimestamp(psutil.boot_time())
    delta = datetime.now() - boot
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes, _ = divmod(rem, 60)
    parts = []
    if days:
        parts.append(f"{days}j")
    if hours:
        parts.append(f"{hours}h")
    parts.append(f"{minutes}min")
    return " ".join(parts)


def get_battery() -> tuple[float, bool]:
    bat = psutil.sensors_battery()
    if bat is None:
        return -1, False
    return bat.percent, bat.power_plugged


def get_disk() -> tuple[float, float, float]:
    usage = shutil.disk_usage("/")
    total = usage.total / 1024**3
    used = usage.used / 1024**3
    percent = (usage.used / usage.total) * 100
    return used, total, percent


def get_network() -> tuple[float, float]:
    counters = psutil.net_io_counters()
    sent = counters.bytes_sent / 1024**2
    recv = counters.bytes_recv / 1024**2
    return sent, recv


def compute_health(cpu: float, ram_pct: float, disk_pct: float,
                   battery_pct: float, temp_str: str) -> tuple[int, str]:
    score = 100

    if cpu > 90:
        score -= 30
    elif cpu > 70:
        score -= 15
    elif cpu > 50:
        score -= 5

    if ram_pct > 90:
        score -= 25
    elif ram_pct > 75:
        score -= 10
    elif ram_pct > 60:
        score -= 5

    if disk_pct > 90:
        score -= 25
    elif disk_pct > 75:
        score -= 10
    elif disk_pct > 60:
        score -= 5

    if 0 <= battery_pct < 10:
        score -= 15
    elif 0 <= battery_pct < 20:
        score -= 5

    try:
        temp_val = float(temp_str.replace("°C", ""))
        if temp_val > 95:
            score -= 20
        elif temp_val > 80:
            score -= 10
        elif temp_val > 70:
            score -= 5
    except ValueError:
        pass

    score = max(0, min(100, score))

    if score >= 90:
        label = "Systeme Optimal"
    elif score >= 70:
        label = "Systeme Correct"
    elif score >= 50:
        label = "Attention Requise"
    else:
        label = "Etat Critique"

    return score, label


def send_notification(title: str, message: str) -> None:
    script = f'display notification "{message}" with title "{title}"'
    subprocess.run(["osascript", "-e", script], check=False)


def log_alert(cpu_percent: float, temp: str) -> None:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = (f"[{timestamp}] ALERTE CPU : {cpu_percent:.1f}% "
            f"| Temp : {temp} (seuil : {CPU_THRESHOLD}%)\n")
    with open(LOG_FILE, "a") as f:
        f.write(line)
    send_notification(
        "SysDash — Alerte CPU",
        f"CPU a {cpu_percent:.1f}% — {temp} (seuil {CPU_THRESHOLD}%)"
    )


def print_dashboard(cpu: float, ram, temp: str, disk_used: float,
                    disk_total: float, disk_pct: float,
                    bat_pct: float, bat_plug: bool,
                    net_sent: float, net_recv: float,
                    uptime: str, score: int, label: str) -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    sep = "=" * WIDTH
    thin = "-" * WIDTH

    bat_str = "N/A (desktop)" if bat_pct < 0 else f"{bat_pct:.0f}%"
    if bat_pct >= 0:
        bat_str += " (secteur)" if bat_plug else " (batterie)"

    lines = [
        "",
        sep,
        f"  SysDash Pro               {ts}",
        sep,
        f"  CPU        : {cpu:5.1f}%           Temp : {temp}",
        f"  RAM        : {ram.percent:5.1f}%"
        f"           {ram.used / 1024**3:.1f} Go / {ram.total / 1024**3:.1f} Go",
        thin,
        f"  Disque     : {disk_pct:5.1f}%"
        f"           {disk_used:.1f} Go / {disk_total:.1f} Go",
        f"  Batterie   : {bat_str}",
        thin,
        f"  Reseau TX  : {net_sent:10.1f} Mo",
        f"  Reseau RX  : {net_recv:10.1f} Mo",
        f"  Uptime     : {uptime}",
        sep,
        f"  Sante : {score}/100 - {label}",
        sep,
    ]
    print("\n".join(lines))


def monitor() -> None:
    print(f"Surveillance demarree (intervalle : {INTERVAL}s, "
          f"seuil CPU : {CPU_THRESHOLD}%)")
    print("=" * WIDTH)
    try:
        while True:
            cpu = psutil.cpu_percent(interval=1)
            ram = psutil.virtual_memory()
            temp = get_cpu_temperature()
            disk_used, disk_total, disk_pct = get_disk()
            bat_pct, bat_plug = get_battery()
            net_sent, net_recv = get_network()
            uptime = get_uptime()

            score, label = compute_health(
                cpu, ram.percent, disk_pct, bat_pct, temp
            )

            print_dashboard(
                cpu, ram, temp,
                disk_used, disk_total, disk_pct,
                bat_pct, bat_plug,
                net_sent, net_recv,
                uptime, score, label,
            )

            if cpu > CPU_THRESHOLD:
                log_alert(cpu, temp)
                print(f"  !! Alerte enregistree dans {LOG_FILE}")

            time.sleep(INTERVAL - 1)
    except KeyboardInterrupt:
        print("\nSurveillance arretee.")


if __name__ == "__main__":
    monitor()
