# SysDash

A lightweight system monitoring tool for macOS (Apple Silicon) featuring a command-line monitor and a local web dashboard. Tracks CPU usage, RAM usage, and CPU temperature in real time.

## Features

- **Real-time metrics**: CPU %, RAM % (with GB used/total), CPU temperature (°C)
- **CLI monitor** (`monitor.py`): prints readings every 5 seconds, logs alerts to `alerts.log` and sends a native macOS notification when CPU exceeds 80%
- **Web dashboard** (`app.py`): clean dark-themed page with animated progress bars and a manual refresh button
- **Apple Silicon support**: reads temperature sensors via [`macmon`](https://github.com/vladkens/macmon) — no `sudo` required

## Requirements

- macOS (Apple Silicon M1/M2/M3/M4/M5)
- Python 3.9+
- [Homebrew](https://brew.sh)

## Installation

```bash
# Clone the repository
git clone <repo-url>
cd SysDash

# Create a virtual environment and install Python dependencies
python3 -m venv venv
source venv/bin/activate
pip install psutil flask

# Install macmon for temperature readings
brew install macmon
```

## Usage

### Command-line monitor

```bash
venv/bin/python3 -u monitor.py
```

Sample output:
```
Surveillance démarrée (intervalle : 5s, seuil CPU : 80.0%)
------------------------------------------------------------
[00:10:04]  CPU :   5.6%  |  RAM :  73.9%  (5.8 Go / 16.0 Go)  |  Temp : 29.5°C
```

Press `Ctrl+C` to stop. Alerts are appended to `alerts.log` when CPU exceeds 80%, and a system notification is triggered.

### Web dashboard

```bash
venv/bin/python3 app.py
```

Then open [http://127.0.0.1:8000](http://127.0.0.1:8000) in your browser and click the **Actualiser** button to fetch the current system metrics. Each click queries the `/api/stats` endpoint and updates the cards with the latest CPU, RAM, and temperature values.

> Note: port 8000 is used instead of 5000 because macOS reserves port 5000 for AirPlay Receiver.

To stop the server: `pkill -f "python3 app.py"`.

## Project structure

```
SysDash/
├── monitor.py          # CLI monitor with alerts
├── app.py              # Flask web server
├── templates/
│   └── index.html      # Dashboard UI
├── alerts.log          # CPU alert log (auto-generated)
├── venv/               # Python virtual environment
├── .gitignore
└── README.md
```

## Configuration

Edit the constants at the top of `monitor.py`:

| Constant        | Default | Description                            |
|-----------------|---------|----------------------------------------|
| `CPU_THRESHOLD` | `80.0`  | CPU usage threshold for alerts (%)     |
| `INTERVAL`      | `5`     | Polling interval in seconds            |
| `LOG_FILE`      | `alerts.log` | Path to the alert log file        |

## License

MIT
