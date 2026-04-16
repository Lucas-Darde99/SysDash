from flask import Flask, jsonify, render_template
import psutil

from monitor import (
    get_cpu_temperature, get_disk, get_battery,
    get_network, get_uptime, compute_health,
)

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/stats")
def stats():
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory()
    temp = get_cpu_temperature()
    disk_used, disk_total, disk_pct = get_disk()
    bat_pct, bat_plug = get_battery()
    net_sent, net_recv = get_network()
    uptime = get_uptime()
    score, label = compute_health(cpu, ram.percent, disk_pct, bat_pct, temp)

    return jsonify({
        "cpu_percent": cpu,
        "ram_percent": ram.percent,
        "ram_used_gb": round(ram.used / 1024**3, 1),
        "ram_total_gb": round(ram.total / 1024**3, 1),
        "cpu_temp": temp,
        "disk_used_gb": round(disk_used, 1),
        "disk_total_gb": round(disk_total, 1),
        "disk_percent": round(disk_pct, 1),
        "battery_percent": round(bat_pct, 1),
        "battery_plugged": bat_plug,
        "net_sent_mb": round(net_sent, 1),
        "net_recv_mb": round(net_recv, 1),
        "uptime": uptime,
        "health_score": score,
        "health_label": label,
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)
