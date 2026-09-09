#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════╗
║   Mushroom Farm IoT Dashboard                ║
║   Flask backend + embedded HTML frontend     ║
╠══════════════════════════════════════════════╣
║  Sensors  : Temperature  · Humidity          ║
║             Light        · CO₂               ║
║             Soil Moisture                    ║
║  Actuators: Humidifier (Misting)             ║
╠══════════════════════════════════════════════╣
║  Install  : pip install flask flask-cors     ║
║  Run      : python mushroom_dashboard.py     ║
║  Open     : http://localhost:5000            ║
╚══════════════════════════════════════════════╝
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import random
import math
from datetime import datetime

app = Flask(__name__)
CORS(app)

# ═══════════════════════════════════════════════════════════
#  In-memory state  (swap _simulate() with real hardware reads)
# ═══════════════════════════════════════════════════════════
_sensor = {
    "temperature":   24.5,
    "humidity":      85.0,
    "light":         420,
    "co2":           650,
    "soil_moisture": 62.0,
    "timestamp":     "",
}

_actuators = {
    "humidifier": False,
}

_tick = 0   # internal time counter for smooth simulation waves


# ═══════════════════════════════════════════════════════════
#  Realistic simulation  (replace body of _simulate()
#  with DHT22 / MQ-135 / BH1750 / capacitive soil reads)
# ═══════════════════════════════════════════════════════════
def _simulate() -> dict:
    global _tick
    _tick += 1
    t = _tick * 0.12
    return {
        "temperature":   round(24.5 + 3.0 * math.sin(t * 0.30)       + random.gauss(0, 0.2),  1),
        "humidity":      round(82.0 + 6.0 * math.sin(t * 0.20 + 1.0) + random.gauss(0, 0.4),  1),
        "light":         max(0,   int(420 + 180 * math.sin(t * 0.15)  + random.gauss(0, 15))),
        "co2":           max(380, int(620 + 220 * math.sin(t * 0.18 + 2.0) + random.gauss(0, 25))),
        "soil_moisture": round(62.0 + 7.0 * math.sin(t * 0.10 + 0.5) + random.gauss(0, 0.3),  1),
        "timestamp":     datetime.now().strftime("%H:%M:%S"),
    }


# ═══════════════════════════════════════════════════════════
#  Routes
# ═══════════════════════════════════════════════════════════
@app.route("/")
def index():
    return DASHBOARD_HTML


@app.route("/api/sensors", methods=["GET"])
def get_sensors():
    global _sensor
    _sensor = _simulate()
    return jsonify(_sensor)


@app.route("/api/sensors", methods=["POST"])
def post_sensors():
    """Receive sensor readings from real hardware (ESP32 / Arduino)."""
    global _sensor
    data = request.get_json(force=True) or {}
    allowed = set(_sensor) - {"timestamp"}
    _sensor.update({k: v for k, v in data.items() if k in allowed})
    _sensor["timestamp"] = datetime.now().strftime("%H:%M:%S")
    return jsonify({"status": "ok", "data": _sensor})


@app.route("/api/actuators", methods=["GET"])
def get_actuators():
    return jsonify(_actuators)


@app.route("/api/actuator", methods=["POST"])
def set_actuator():
    """Control the humidifier.  Body: {"device":"humidifier","state":true}"""
    data = request.get_json(force=True) or {}
    device = data.get("device")
    state  = data.get("state")

    if device not in _actuators:
        return jsonify({"error": f"Unknown device '{device}'. Valid: {list(_actuators.keys())}"}), 400
    if not isinstance(state, bool):
        return jsonify({"error": "'state' must be a boolean (true / false)"}), 400

    _actuators[device] = state
    label = "ON  ✓" if state else "OFF"
    print(f"  [{datetime.now().strftime('%H:%M:%S')}]  {device.upper():<12} → {label}")
    return jsonify({"ok": True, "device": device, "state": state})


# ═══════════════════════════════════════════════════════════
#  Embedded HTML dashboard  (Mushroom Theme)
# ═══════════════════════════════════════════════════════════
DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Mushroom Farm Dashboard</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet" />
  <style>
    :root {
      --bg: #08111f;
      --bg-soft: #0d1728;
      --surface: #101c2f;
      --surface-2: #13233b;
      --surface-3: #172845;
      --border: rgba(148, 163, 184, 0.18);
      --border-strong: rgba(148, 163, 184, 0.34);
      --text: #e5eefc;
      --muted: #8ea0bf;
      --primary: #4f8cff;
      --primary-2: #7c5cff;
      --teal: #2dd4bf;
      --success: #38bdf8;
      --warning: #f59e0b;
      --danger: #fb7185;
      --radius: 18px;
      --shadow: 0 22px 48px rgba(0, 0, 0, 0.28);
      --temp: #ff6b6b;
      --hum: #38bdf8;
      --light: #fbbf24;
      --co2: #a78bfa;
      --soil: #34d399;
    }

    *, *::before, *::after { box-sizing: border-box; }
    * { margin: 0; padding: 0; }

    body {
      font-family: 'Inter', 'Segoe UI', sans-serif;
      background:
        radial-gradient(circle at top left, rgba(79,140,255,0.18), transparent 28%),
        radial-gradient(circle at 80% 10%, rgba(124,92,255,0.16), transparent 22%),
        radial-gradient(circle at bottom right, rgba(45,212,191,0.11), transparent 28%),
        var(--bg);
      color: var(--text);
      min-height: 100vh;
    }

    .app-shell {
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr);
      min-height: 100vh;
    }

    .sidebar {
      position: sticky;
      top: 0;
      align-self: start;
      height: 100vh;
      padding: 22px;
      background: linear-gradient(180deg, rgba(16,28,47,0.98), rgba(9,17,31,0.98));
      border-right: 1px solid rgba(148, 163, 184, 0.14);
      display: flex;
      flex-direction: column;
      gap: 20px;
    }
    
    .sidebar.collapsed {
      width: 96px;
      padding-left: 16px;
      padding-right: 16px;
    }
    
    .sidebar.collapsed .brand-block p,
    .sidebar.collapsed .sidebar-section-title,
    .sidebar.collapsed .nav-item span,
    .sidebar.collapsed .sidebar-card,
    .sidebar.collapsed .sidebar-card *:not(h4),
    .sidebar.collapsed .sidebar-meta {
      display: none;
    }
    
    .sidebar.collapsed .brand-block {
      padding: 12px;
    }
    
    .sidebar-toggle {
      align-self: flex-end;
      width: 38px;
      height: 38px;
      border-radius: 12px;
      border: 1px solid rgba(148, 163, 184, 0.16);
      background: rgba(255,255,255,0.04);
      color: #e5eefc;
      cursor: pointer;
      font-size: 1rem;
    }
    
    .sidebar.collapsed .sidebar-toggle {
      align-self: center;
    }

    .brand-block {
      padding: 18px;
      border-radius: 20px;
      background: linear-gradient(135deg, rgba(79,140,255,0.20), rgba(124,92,255,0.12));
      border: 1px solid rgba(148, 163, 184, 0.16);
    }

    .brand-block h1 {
      font-size: 1.05rem;
      font-weight: 800;
      margin-bottom: 8px;
      letter-spacing: -0.02em;
    }

    .brand-block p {
      color: var(--muted);
      font-size: 0.88rem;
      line-height: 1.5;
    }

    .sidebar-section-title {
      color: #c7d2e5;
      font-size: 0.72rem;
      font-weight: 800;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      margin-bottom: 12px;
    }

    .nav-list {
      display: grid;
      gap: 8px;
    }

    .nav-item {
      border: 1px solid rgba(148, 163, 184, 0.1);
      background: rgba(255, 255, 255, 0.02);
      border-radius: 14px;
      padding: 12px 14px;
      color: #d9e5f6;
      font-size: 0.9rem;
    }

    .nav-item {
      width: 100%;
      text-align: left;
      appearance: none;
      cursor: pointer;
    }

    .nav-item.active {
      background: linear-gradient(135deg, rgba(79,140,255,0.22), rgba(45,212,191,0.12));
      border-color: rgba(79,140,255,0.35);
      box-shadow: 0 10px 24px rgba(79,140,255,0.14);
    }

    .btn-row .btn {
      border: 1px solid transparent;
      border-radius: 12px;
      padding: 11px 16px;
      font: inherit;
      font-size: 0.88rem;
      font-weight: 700;
      cursor: pointer;
      transition: transform 0.18s ease, box-shadow 0.18s ease, filter 0.18s ease;
    }

    .btn-row .btn:hover {
      transform: translateY(-1px);
      filter: brightness(1.04);
    }

    .btn-row .btn:active {
      transform: translateY(0);
    }

    .btn-primary {
      background: linear-gradient(135deg, var(--primary), var(--primary-2));
      color: #fff;
      box-shadow: 0 10px 20px rgba(79, 140, 255, 0.22);
    }

    .btn-secondary {
      background: linear-gradient(135deg, rgba(255,255,255,0.94), rgba(221,230,242,0.92));
      color: var(--text);
      border-color: var(--border-strong);
    }

    .nav-item:focus-visible,
    .btn:focus-visible {
      outline: 2px solid rgba(56,189,248,0.7);
      outline-offset: 2px;
    }
    
    .toggle-control {
      display: inline-flex;
      align-items: center;
      gap: 12px;
      cursor: pointer;
      user-select: none;
      width: 100%;
      justify-content: space-between;
      padding: 4px 0;
    }
    
    .toggle-control input {
      position: absolute;
      opacity: 0;
      pointer-events: none;
    }
    
    .toggle-track {
      width: 68px;
      height: 36px;
      border-radius: 999px;
      background: rgba(148,163,184,0.2);
      border: 1px solid rgba(148,163,184,0.24);
      position: relative;
      flex: 0 0 auto;
      transition: background 0.2s ease, border-color 0.2s ease;
    }
    
    .toggle-thumb {
      position: absolute;
      top: 4px;
      left: 4px;
      width: 28px;
      height: 28px;
      border-radius: 50%;
      background: linear-gradient(180deg, #ffffff, #dce6f4);
      box-shadow: 0 8px 18px rgba(0,0,0,0.2);
      transition: transform 0.22s ease, background 0.22s ease;
    }
    
    .toggle-control input:checked + .toggle-track {
      background: linear-gradient(135deg, rgba(79,140,255,0.95), rgba(45,212,191,0.82));
      border-color: rgba(79,140,255,0.5);
    }
    
    .toggle-control input:checked + .toggle-track .toggle-thumb {
      transform: translateX(32px);
      background: linear-gradient(180deg, #ffffff, #cfe7ff);
    }
    
    .toggle-text {
      font-size: 0.88rem;
      font-weight: 700;
      color: #eef4ff;
      min-width: 88px;
      text-align: right;
    }

    .sidebar-card {
      margin-top: auto;
      padding: 16px;
      border-radius: 16px;
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(148, 163, 184, 0.14);
    }

    .sidebar-card h4 {
      font-size: 0.92rem;
      margin-bottom: 6px;
    }

    .sidebar-card p {
      color: var(--muted);
      font-size: 0.84rem;
      line-height: 1.5;
    }

    .sidebar-meta {
      display: grid;
      gap: 10px;
      margin-top: 12px;
      color: #dbe7fa;
      font-size: 0.86rem;
    }

    .meta-row {
      display: flex;
      justify-content: space-between;
      gap: 14px;
    }

    .meta-row span:last-child {
      color: var(--muted);
      text-align: right;
    }

    .content {
      min-width: 0;
      padding: 20px 20px 26px;
    }

    .topbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      margin-bottom: 18px;
    }

    .topbar h2 {
      font-size: 1.35rem;
      letter-spacing: -0.03em;
      margin-bottom: 6px;
    }

    .topbar p {
      color: var(--muted);
      font-size: 0.94rem;
      line-height: 1.5;
    }

    .header-meta {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }

    .status-pill {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 10px 14px;
      border-radius: 999px;
      background: rgba(56, 189, 248, 0.08);
      color: #a5e8ff;
      border: 1px solid rgba(56, 189, 248, 0.18);
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }

    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #38bdf8;
      box-shadow: 0 0 0 6px rgba(56, 189, 248, 0.12);
    }

    .time-block {
      text-align: right;
      line-height: 1.2;
    }

    #clock {
      font-size: 0.98rem;
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }

    #date-disp {
      color: var(--muted);
      font-size: 0.82rem;
      margin-top: 2px;
    }

    .page-grid {
      display: grid;
      gap: 18px;
    }

    .section-title {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 14px;
      margin-bottom: 12px;
    }

    .section-title h3 {
      font-size: 1rem;
      font-weight: 800;
      letter-spacing: -0.01em;
    }

    .section-title span {
      color: var(--muted);
      font-size: 0.84rem;
    }

    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(5, minmax(0, 1fr));
      gap: 14px;
    }

    .kpi-card,
    .panel,
    .table-card,
    .chart-card {
      background: linear-gradient(180deg, rgba(19,35,59,0.98), rgba(16,28,47,0.98));
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
    }

    .kpi-card {
      padding: 16px;
      border-top: 4px solid var(--accent, var(--primary));
      min-height: 132px;
    }

    .kpi-label {
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.13em;
      font-size: 0.7rem;
      font-weight: 800;
      margin-bottom: 12px;
    }

    .kpi-value {
      font-size: 2rem;
      line-height: 1;
      font-weight: 800;
      letter-spacing: -0.04em;
      font-variant-numeric: tabular-nums;
    }

    .kpi-unit {
      color: var(--muted);
      font-size: 0.88rem;
      margin-left: 4px;
      font-weight: 600;
    }

    .kpi-footer {
      margin-top: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 5px 10px;
      border-radius: 999px;
      font-size: 0.7rem;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      white-space: nowrap;
    }

    .badge-good { background: rgba(56,189,248,0.12); color: #8ad9ff; }
    .badge-warning { background: rgba(245,158,11,0.12); color: #f8c56b; }
    .badge-danger { background: rgba(251,113,133,0.12); color: #ff9aad; }

    .mini-trend {
      width: 84px;
      height: 44px;
      opacity: 0.9;
    }

    .two-col {
      display: grid;
      grid-template-columns: 1.55fr 0.9fr;
      gap: 16px;
      align-items: start;
    }

    .panel {
      padding: 18px;
    }

    .panel h4 {
      font-size: 0.98rem;
      margin-bottom: 10px;
    }

    .panel p {
      color: var(--muted);
      font-size: 0.9rem;
      line-height: 1.65;
    }

    .compact-sensors {
      display: grid;
      gap: 12px;
    }

    .sensor-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 14px;
      padding: 12px 14px;
      border-radius: 14px;
      background: rgba(255,255,255,0.03);
      border: 1px solid rgba(148,163,184,0.12);
    }

    .sensor-row strong {
      display: block;
      font-size: 0.9rem;
      margin-bottom: 3px;
    }

    .sensor-row span {
      color: var(--muted);
      font-size: 0.8rem;
    }

    .sensor-row .value {
      font-size: 1.15rem;
      font-weight: 800;
      font-variant-numeric: tabular-nums;
      color: #eef4ff;
    }

    .chart-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 16px;
    }

    .chart-card {
      padding: 18px;
      min-height: 320px;
    }

    .chart-title {
      display: flex;
      align-items: center;
      gap: 10px;
      margin-bottom: 16px;
      font-size: 0.92rem;
      font-weight: 700;
    }

    .chart-dot {
      width: 10px;
      height: 10px;
      border-radius: 50%;
      flex: 0 0 auto;
    }

    canvas { max-height: 245px; }

    .table-card {
      overflow-x: auto;
      padding: 0;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 720px;
    }

    th, td {
      text-align: left;
      padding: 11px 14px;
      border-bottom: 1px solid rgba(148,163,184,0.14);
      font-size: 0.86rem;
    }

    th {
      background: rgba(255,255,255,0.03);
      color: #b7c4db;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      font-size: 0.7rem;
      font-weight: 800;
    }

    tbody tr:hover td { background: rgba(255,255,255,0.03); }
    .td-name { font-weight: 700; color: #eef4ff; }
    .td-range, .td-unit { color: var(--muted); }
    .td-curr { font-variant-numeric: tabular-nums; font-weight: 700; color: #eef4ff; }

    .footer-note {
      margin-top: 4px;
      color: var(--muted);
      font-size: 0.8rem;
    }

    .footer-bar {
      margin-top: 18px;
      display: flex;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 0.82rem;
    }

    @media (max-width: 1220px) {
      .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .chart-grid { grid-template-columns: 1fr; }
      .two-col { grid-template-columns: 1fr; }
    }

    @media (max-width: 920px) {
      .app-shell { grid-template-columns: 1fr; }
      .sidebar {
        position: relative;
        height: auto;
      }
    }

    @media (max-width: 640px) {
      .content, .sidebar { padding-left: 14px; padding-right: 14px; }
      .topbar { flex-direction: column; align-items: flex-start; }
      .header-meta { width: 100%; justify-content: space-between; }
      .kpi-grid { grid-template-columns: 1fr; }
      .section-title { flex-direction: column; align-items: flex-start; }
      .kpi-value { font-size: 1.75rem; }
      .panel, .chart-card { padding: 16px; }
      table { min-width: 640px; }
    }
  </style>
</head>

<body>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand-block">
        <h1>Mushroom Farm</h1>
        <p>Enterprise monitoring for cultivation conditions, live status, and humidifier control.</p>
      </div>

      <button class="sidebar-toggle" id="sidebar-toggle" type="button" aria-label="Collapse sidebar">⟨</button>

      <div>
        <div class="sidebar-section-title">Navigation</div>
        <div class="nav-list">
          <button class="nav-item active" type="button" data-target="overview"><span>Overview</span></button>
          <button class="nav-item" type="button" data-target="sensors"><span>Sensors</span></button>
          <button class="nav-item" type="button" data-target="actuators"><span>Actuator Control</span></button>
          <button class="nav-item" type="button" data-target="trends"><span>Historical Trends</span></button>
          <button class="nav-item" type="button" data-target="reference"><span>Growth Reference</span></button>
        </div>
      </div>

      <div>
        <div class="sidebar-section-title">System Status</div>
        <div class="sidebar-card">
          <h4>Live Monitoring</h4>
          <p>Continuous environmental updates with a compact operational summary.</p>
          <div class="sidebar-meta">
            <div class="meta-row"><span>Connection</span><span id="side-connection">Online</span></div>
            <div class="meta-row"><span>Last update</span><span id="side-last">--:--:--</span></div>
            <div class="meta-row"><span>Humidifier</span><span id="side-hum">Standby</span></div>
          </div>
        </div>
      </div>
    </aside>

    <div class="content">
      <div class="topbar" id="overview">
        <div>
          <h2>Environmental Overview</h2>
          <p>Monitor conditions, review trends, and control the humidifier from a clean operational dashboard.</p>
        </div>
        <div class="header-meta">
          <div class="time-block">
            <div id="clock">00:00:00</div>
            <div id="date-disp">Loading...</div>
          </div>
          <div class="status-pill"><span class="status-dot"></span>Live System</div>
        </div>
      </div>

      <div class="page-grid">
        <section id="sensors">
          <div class="section-title">
            <h3>Summary KPIs</h3>
            <span>Snapshot of current growing conditions</span>
          </div>
          <div class="kpi-grid">
            <div class="kpi-card" id="card-temp" style="--accent: var(--temp)">
              <div class="kpi-label">Temperature</div>
              <div><span class="kpi-value" id="val-temp">—</span><span class="kpi-unit">°C</span></div>
                <div class="kpi-footer"><div class="footer-note">Target: 18-28°C</div><span class="badge badge-good" id="badge-temp">Pending</span></div>
            </div>
            <div class="kpi-card" id="card-hum" style="--accent: var(--hum)">
              <div class="kpi-label">Humidity</div>
              <div><span class="kpi-value" id="val-hum">—</span><span class="kpi-unit">%</span></div>
                <div class="kpi-footer"><div class="footer-note">Target: 80-95%</div><span class="badge badge-good" id="badge-hum">Pending</span></div>
            </div>
            <div class="kpi-card" id="card-light" style="--accent: var(--light)">
              <div class="kpi-label">Light Intensity</div>
              <div><span class="kpi-value" id="val-light">—</span><span class="kpi-unit">lux</span></div>
                <div class="kpi-footer"><div class="footer-note">Target: 200-600 lux</div><span class="badge badge-good" id="badge-light">Pending</span></div>
            </div>
            <div class="kpi-card" id="card-co2" style="--accent: var(--co2)">
              <div class="kpi-label">CO2 Concentration</div>
              <div><span class="kpi-value" id="val-co2">—</span><span class="kpi-unit">ppm</span></div>
                <div class="kpi-footer"><div class="footer-note">Target: 400-900 ppm</div><span class="badge badge-good" id="badge-co2">Pending</span></div>
            </div>
            <div class="kpi-card" id="card-soil" style="--accent: var(--soil)">
              <div class="kpi-label">Substrate Moisture</div>
              <div><span class="kpi-value" id="val-soil">—</span><span class="kpi-unit">%</span></div>
                <div class="kpi-footer"><div class="footer-note">Target: 55-80%</div><span class="badge badge-good" id="badge-soil">Pending</span></div>
            </div>
          </div>
        </section>

        <section class="two-col" id="actuators">
          <div class="panel">
            <div class="section-title">
              <h3>Actuator Status</h3>
              <span>Current misting state</span>
            </div>
            <div class="compact-sensors">
              <div class="sensor-row" id="act-humidifier">
                <div>
                  <strong>Humidifier</strong>
                  <span>Shows the current misting system state.</span>
                </div>
                <div style="text-align:right;">
                  <div class="value" id="humidifier-status-text">OFF</div>
                  <div class="footer-note">Current state</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section id="trends">
          <div class="section-title">
            <h3>Historical Trends</h3>
            <span>Recent sensor history</span>
          </div>
          <div class="chart-grid">
            <div class="chart-card">
              <div class="chart-title"><span class="chart-dot" style="background: var(--temp)"></span>Temperature</div>
              <canvas id="chartTemp"></canvas>
            </div>
            <div class="chart-card">
              <div class="chart-title"><span class="chart-dot" style="background: var(--hum)"></span>Humidity</div>
              <canvas id="chartHum"></canvas>
            </div>
            <div class="chart-card">
              <div class="chart-title"><span class="chart-dot" style="background: var(--co2)"></span>CO2</div>
              <canvas id="chartCO2"></canvas>
            </div>
            <div class="chart-card">
              <div class="chart-title"><span class="chart-dot" style="background: var(--soil)"></span>Soil Moisture</div>
              <canvas id="chartSoil"></canvas>
            </div>
          </div>
        </section>

        <section id="reference">
          <div class="section-title">
            <h3>Optimal Growth Conditions</h3>
            <span>Compact reference table</span>
          </div>
          <div class="table-card">
            <table>
              <thead>
                <tr>
                  <th>Parameter</th>
                  <th>Minimum</th>
                  <th>Maximum</th>
                  <th>Unit</th>
                  <th>Current</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td class="td-name">Temperature</td>
                  <td class="td-range">18</td>
                  <td class="td-range">28</td>
                  <td class="td-unit">°C</td>
                  <td class="td-curr" id="tbl-temp">—</td>
                  <td id="tbl-badge-temp">—</td>
                </tr>
                <tr>
                  <td class="td-name">Humidity</td>
                  <td class="td-range">80</td>
                  <td class="td-range">95</td>
                  <td class="td-unit">%</td>
                  <td class="td-curr" id="tbl-hum">—</td>
                  <td id="tbl-badge-hum">—</td>
                </tr>
                <tr>
                  <td class="td-name">Light Intensity</td>
                  <td class="td-range">200</td>
                  <td class="td-range">600</td>
                  <td class="td-unit">lux</td>
                  <td class="td-curr" id="tbl-light">—</td>
                  <td id="tbl-badge-light">—</td>
                </tr>
                <tr>
                  <td class="td-name">CO2 Concentration</td>
                  <td class="td-range">400</td>
                  <td class="td-range">900</td>
                  <td class="td-unit">ppm</td>
                  <td class="td-curr" id="tbl-co2">—</td>
                  <td id="tbl-badge-co2">—</td>
                </tr>
                <tr>
                  <td class="td-name">Soil Moisture</td>
                  <td class="td-range">55</td>
                  <td class="td-range">80</td>
                  <td class="td-unit">%</td>
                  <td class="td-curr" id="tbl-soil">—</td>
                  <td id="tbl-badge-soil">—</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        <div class="footer-bar">
          <div>Mushroom Farm Dashboard</div>
          <div>Last updated: <span id="last-ts">—</span></div>
          <div>Flask + Chart.js</div>
        </div>
      </div>
    </div>
  </div>

<script type="module">
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.2/firebase-app.js";

import {
    getDatabase,
    ref,
    query,
    limitToLast,
    onValue
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-database.js";
const firebaseConfig = {

  apiKey: "AIzaSyAP_3vydhQ3PILbEqiAaAJvsR76_o-GJRU",

  authDomain: "fullsystem-a0461.firebaseapp.com",

  databaseURL:
  "https://fullsystem-a0461-default-rtdb.asia-southeast1.firebasedatabase.app",

  projectId: "fullsystem-a0461",

  storageBucket: "fullsystem-a0461.firebasestorage.app",

  messagingSenderId: "88593039184",

  appId: "1:88593039184:web:376b7de9d1fe1b00f7f655"

};

const app = initializeApp(firebaseConfig);

const db = getDatabase(app);
const SENSOR_PATH = 'nofan';
const ENABLE_LOCAL_SENSOR_POLL = false;
/* ── Clock ──────────────────────────────────────── */
function updateClock() {
  const now = new Date();
  document.getElementById('clock').textContent =
    now.toLocaleTimeString('en-GB');
  document.getElementById('date-disp').textContent =
    now.toLocaleDateString('en-GB', { weekday:'short', day:'2-digit', month:'short', year:'numeric' });
}
setInterval(updateClock, 1000);
updateClock();

/* ── Chart.js defaults ──────────────────────────── */
Chart.defaults.color = '#a8b8d6';
Chart.defaults.borderColor = 'rgba(148,163,184,0.22)';
Chart.defaults.font.family = "'Inter', 'Segoe UI', sans-serif";

const MAX_POINTS = 25;

function makeChart(id, label, color) {
  const ctx = document.getElementById(id).getContext('2d');
  const grad = ctx.createLinearGradient(0, 0, 0, 200);
  grad.addColorStop(0, color + '55');
  grad.addColorStop(1, color + '00');
  return new Chart(ctx, {
    type: 'line',
    data: {
      labels: [],
      datasets: [{
        label,
        data: [],
        borderColor: color,
        backgroundColor: grad,
        borderWidth: 2.5,
        fill: true,
        tension: 0.42,
        pointRadius: 3,
        pointBackgroundColor: color,
        pointBorderColor: '#ffffff',
        pointBorderWidth: 2,
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      animation: { duration: 400 },
      plugins: { legend: { display: false } },
      scales: {
        x: {
          ticks: { maxTicksLimit: 8, maxRotation: 0 },
          grid: { color: 'rgba(148,163,184,0.18)' }
        },
        y: {
          ticks: { maxTicksLimit: 6 },
          grid: { color: 'rgba(148,163,184,0.18)' }
        }
      }
    }
  });
}

const chartTemp = makeChart('chartTemp', 'Temperature (°C)', '#e84830');
const chartHum  = makeChart('chartHum',  'Humidity (%)',      '#3090d8');
const chartCO2  = makeChart('chartCO2',  'CO₂ (ppm)',         '#9050c8');
const chartSoil = makeChart('chartSoil', 'Soil Moisture (%)', '#40905c');

function pushData(chart, label, value) {
  chart.data.labels.push(label);
  chart.data.datasets[0].data.push(value);
  if (chart.data.labels.length > MAX_POINTS) {
    chart.data.labels.shift();
    chart.data.datasets[0].data.shift();
  }
  chart.update('none');
}

function clearChart(chart) {
  chart.data.labels = [];
  chart.data.datasets[0].data = [];
}

function renderHistory(records) {
  clearChart(chartTemp);
  clearChart(chartHum);
  clearChart(chartCO2);
  clearChart(chartSoil);

  const recentRecords = records.slice(-MAX_POINTS);
  recentRecords.forEach((record, index) => {
    const label = record.timestamp_readable || record.timestamp || record.time || `#${index + 1}`;
    const temp = Number(record.temperature ?? record.temp ?? NaN);
    const hum = Number(record.humidity ?? record.hum ?? NaN);
    const co2 = Number(record.co2 ?? record.co2_ppm ?? NaN);
    const soil = Number(record.soil_moisture ?? record.soil_raw ?? record.soil ?? NaN);

    if (Number.isFinite(temp)) pushData(chartTemp, label, temp);
    if (Number.isFinite(hum)) pushData(chartHum, label, hum);
    if (Number.isFinite(co2)) pushData(chartCO2, label, co2);
    if (Number.isFinite(soil)) pushData(chartSoil, label, soil);
  });
}

/* ── Arc gauge helper ────────────────────────────
   Half-arc path length = π × r = π × 42 ≈ 131.95
*/
const ARC_LEN = 131.95;

function setArc(id, ratio) {
  const arc = document.getElementById('arc-' + id);
  if (!arc) return;
  const offset = ARC_LEN * (1 - Math.min(1, Math.max(0, ratio)));
  arc.style.strokeDashoffset = offset.toFixed(2);
}

/* ── Status badge helper ─────────────────────── */
const RANGES = {
  temp:  { min: 15,  max: 24,   warn_lo: 13,  warn_hi: 26  },
  hum:   { min: 85,  max: 95,   warn_lo: 80,  warn_hi: 98  },
  light: { min: 100, max: 200,  warn_lo: 70,  warn_hi: 250 },
  co2:   { min: 500, max: 800,  warn_lo: 420, warn_hi: 950 },
  soil:  { min: 55,  max: 80,   warn_lo: 45,  warn_hi: 90  },
};

function getBadge(key, val) {
  const r = RANGES[key];
  if (!r) return { cls: 'badge-good', txt: 'OK' };
  if (key === 'soil') {
    if (val < r.min) return { cls: 'badge-warning', txt: 'Dry' };
    if (val > r.max) return { cls: 'badge-warning', txt: 'Wet' };
    return { cls: 'badge-good', txt: 'Wet' };
  }
  if (val >= r.min && val <= r.max)           return { cls: 'badge-good',    txt: 'Ideal'   };
  if (val >= r.warn_lo && val <= r.warn_hi)   return { cls: 'badge-warning', txt: 'Warning' };
  return                                              { cls: 'badge-danger',  txt: 'Alert'  };
}

function applyBadge(key, val) {
  const b = getBadge(key, val);
  const el = document.getElementById('badge-' + key);
  if (el) { el.className = 'badge ' + b.cls; el.textContent = b.txt; }
  // table badge
  const tel = document.getElementById('tbl-badge-' + key);
  if (tel) { tel.innerHTML = `<span class="badge ${b.cls}">${b.txt}</span>`; }
}

/* ── Fetch sensor data ───────────────────────── */
const sideConnectionEl = document.getElementById('side-connection');
const sensorRef = ref(db, SENSOR_PATH);

const SENSOR_KEYS = ['temperature', 'temp', 'humidity', 'hum', 'light', 'co2', 'co2_ppm', 'soil_moisture', 'soil_raw', 'soil'];

function containsSensorFields(node) {
  if (!node || typeof node !== 'object') return false;
  return SENSOR_KEYS.some((k) => Object.prototype.hasOwnProperty.call(node, k));
}

function pickLatestSensorPayload(node, depth = 0) {
  if (!node || typeof node !== 'object') return null;
  if (containsSensorFields(node)) return node;
  if (depth > 4) return null;

  const keys = Object.keys(node);
  if (!keys.length) return null;

  // Prefer the newest-like key when data is time/push-key based.
  const candidateKeys = keys.slice().sort();
  for (let i = candidateKeys.length - 1; i >= 0; i -= 1) {
    const child = node[candidateKeys[i]];
    const resolved = pickLatestSensorPayload(child, depth + 1);
    if (resolved) return resolved;
  }

  return null;
}

function collectSensorRecords(node, records = [], seen = new Set(), depth = 0) {
  if (!node || typeof node !== 'object' || depth > 5) return records;

  if (containsSensorFields(node)) {
    const signature = JSON.stringify({
      temperature: node.temperature ?? node.temp,
      humidity: node.humidity ?? node.hum,
      light: node.light,
      co2: node.co2 ?? node.co2_ppm,
      soil_moisture: node.soil_moisture ?? node.soil_raw ?? node.soil,
      timestamp: node.timestamp_readable ?? node.timestamp ?? node.time,
    });
    if (!seen.has(signature)) {
      seen.add(signature);
      records.push(node);
    }
  }

  const keys = Object.keys(node).slice().sort();
  keys.forEach((key) => {
    collectSensorRecords(node[key], records, seen, depth + 1);
  });

  return records;
}

onValue(sensorRef, (snapshot) => {
  const data = snapshot.val();
  if (!data) {
    if (sideConnectionEl) sideConnectionEl.textContent = 'No data';
    console.warn('[Firebase] Empty snapshot at path:', SENSOR_PATH);
    return;
  }

  const records = collectSensorRecords(data);
  const d = pickLatestSensorPayload(data);
  if (!d) {
    if (sideConnectionEl) sideConnectionEl.textContent = 'Invalid data';
    console.warn('[Firebase] No sensor fields found at path:', SENSOR_PATH, data);
    return;
  }

  if (sideConnectionEl) sideConnectionEl.textContent = 'Online';
  console.log('[Firebase] Resolved payload from path:', SENSOR_PATH, d);
  renderHistory(records.length ? records : [d]);
  updateDashboard(d);
}, (error) => {
  if (sideConnectionEl) sideConnectionEl.textContent = 'Read blocked';
  console.error('[Firebase] Read failed:', error?.code, error?.message);
});

function updateDashboard(d){

  const temp = Number(d.temperature ?? d.temp ?? NaN);
  const hum = Number(d.humidity ?? d.hum ?? NaN);
  const light = Number(d.light ?? NaN);
  const co2 = Number(d.co2 ?? d.co2_ppm ?? NaN);
  const soil = Number(d.soil_moisture ?? d.soil_raw ?? d.soil ?? NaN);
  const soilStatus = String(d.soil_status ?? d.substrate_status ?? '').trim().toLowerCase();
  const ts = d.timestamp_readable || d.timestamp || d.time || new Date().toLocaleTimeString('en-GB');

  const valueMap = {
    temp: temp,
    hum: hum,
    light: light,
    co2: co2,
    soil: soil,
  };

  Object.entries(valueMap).forEach(([key, value]) => {
    const valueEl = document.getElementById('val-' + key);
    const tableEl = document.getElementById('tbl-' + key);
    const badge = document.getElementById('badge-' + key);
    const valid = Number.isFinite(value);

    if (valueEl) valueEl.textContent = valid ? value.toFixed(key === 'light' || key === 'co2' ? 0 : 1) : '—';
    if (tableEl) tableEl.textContent = valid ? value.toFixed(key === 'light' || key === 'co2' ? 0 : 1) : '—';

    if (valid) {
      applyBadge(key, value);
    } else if (badge) {
      badge.className = 'badge badge-warning';
      badge.textContent = 'No data';
    }
  });

  setArc('temp',  (temp  - 10) / 25);
  setArc('hum',   (hum   - 50) / 50);
  setArc('light', light / 1000);
  setArc('co2',   (co2   - 300) / 900);
  setArc('soil',  soil / 100);

  if (Number.isFinite(soil)) {
    const soilBadge = soilStatus === 'dry' || soil < 55
      ? { cls: 'badge-warning', txt: 'Dry' }
      : { cls: 'badge-good', txt: 'Wet' };
    const soilBadgeEl = document.getElementById('badge-soil');
    const soilTableEl = document.getElementById('tbl-badge-soil');
    if (soilBadgeEl) { soilBadgeEl.className = 'badge ' + soilBadge.cls; soilBadgeEl.textContent = soilBadge.txt; }
    if (soilTableEl) { soilTableEl.innerHTML = `<span class="badge ${soilBadge.cls}">${soilBadge.txt}</span>`; }
  }

  const mistState = d.mist_prediction ?? d.mist_status;

    if (mistState !== undefined) {
    const humidifierState = String(mistState).toUpperCase() === "ON";
    setActuatorUI("humidifier", humidifierState);
  }

  document.getElementById('side-last').textContent = ts;

  const stampEl = document.getElementById('last-ts');
  if (stampEl) stampEl.textContent = ts;

  const timeLabel = new Date().toLocaleTimeString('en-GB', { hour12: false });
  if (Number.isFinite(temp))  pushData(chartTemp, timeLabel, temp);
  if (Number.isFinite(hum))   pushData(chartHum,  timeLabel, hum);
  if (Number.isFinite(co2))   pushData(chartCO2,  timeLabel, co2);
  if (Number.isFinite(soil))  pushData(chartSoil, timeLabel, soil);
}

function updateSensors() {
  if (!ENABLE_LOCAL_SENSOR_POLL) return;
  fetch('/api/sensors')
    .then(r => r.json())
    .then(updateDashboard)
    .catch(e => console.error('Sensor error:', e));
}

/* ── Fetch actuator states ───────────────────── */
function updateActuators() {
  fetch('/api/actuators')
    .then(r => r.json())
    .then(d => {
      setActuatorUI('humidifier', d.humidifier);
    });
}

function setActuatorUI(device, isOn) {
  const card = document.getElementById('act-' + device);
  const text = document.getElementById(device + '-status-text');
  const sideHum = document.getElementById('side-hum');
  if (!card || !text) return;
  if (isOn) {
    card.classList.add('on');
    text.textContent = 'ON';
    if (sideHum) sideHum.textContent = 'ON';
  } else {
    card.classList.remove('on');
    text.textContent = 'OFF';
    if (sideHum) sideHum.textContent = 'OFF';
  }
}

const navButtons = Array.from(document.querySelectorAll('.nav-item[data-target]'));
navButtons.forEach((btn) => {
  btn.addEventListener('click', () => {
    const target = document.getElementById(btn.dataset.target);
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
    navButtons.forEach((item) => item.classList.remove('active'));
    btn.classList.add('active');
  });
});

const sidebar = document.querySelector('.sidebar');
const sidebarToggle = document.getElementById('sidebar-toggle');
if (sidebar && sidebarToggle) {
  sidebarToggle.addEventListener('click', () => {
    sidebar.classList.toggle('collapsed');
    const collapsed = sidebar.classList.contains('collapsed');
    sidebarToggle.textContent = collapsed ? '⟩' : '⟨';
    sidebarToggle.setAttribute('aria-label', collapsed ? 'Expand sidebar' : 'Collapse sidebar');
  });
}

const dashboardSections = ['overview', 'sensors', 'actuators', 'trends', 'reference'];
const sectionObserver = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) {
      const current = navButtons.find((btn) => btn.dataset.target === entry.target.id);
      if (current) {
        navButtons.forEach((item) => item.classList.remove('active'));
        current.classList.add('active');
      }
    }
  });
}, { rootMargin: '-25% 0px -60% 0px', threshold: 0.1 });

dashboardSections.forEach((id) => {
  const section = document.getElementById(id);
  if (section) sectionObserver.observe(section);
});

/* ── Start polling ───────────────────────────── */
updateSensors();
setInterval(updateSensors,   2000);
</script>

</body>
</html>
"""

# ═══════════════════════════════════════════════════════════
#  Entry point
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    print()
    print("  ╔═════════════════════════════════════╗")
    print("  ║   Mushroom Farm Dashboard           ║")
    print("  ╠═════════════════════════════════════╣")
    print("  ║   http://localhost:5000             ║")
    print("  ║   Press Ctrl+C to stop              ║")
    print("  ╚═════════════════════════════════════╝")
    print()
    app.run(debug=True, host="0.0.0.0", port=5000)
