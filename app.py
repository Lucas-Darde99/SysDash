from flask import Flask, jsonify, render_template
import psutil

from monitor import get_cpu_temperature

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/stats")
def stats():
    ram = psutil.virtual_memory()
    return jsonify({
        "cpu_percent": psutil.cpu_percent(interval=0.5),
        "ram_percent": ram.percent,
        "ram_used_gb": round(ram.used / 1024**3, 1),
        "ram_total_gb": round(ram.total / 1024**3, 1),
        "cpu_temp": get_cpu_temperature(),
    })


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=False)
