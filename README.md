# 🛡️ AEGIS — Autonomous Watchdog for Industrial IoT Security

**AEGIS** is a real-time Machine Learning-powered anomaly detection system designed to act as a secondary validation layer between industrial machinery and their connected SIIoT (Smart Industrial Internet of Things) devices. Its goal? To prevent silent failures, detect malware attacks, and ensure operational safety.

---

## 🚨 Problem Statement

> SIIoT devices are increasingly targeted by malware and cyber threats, leading to system failures, data manipulation, and serious safety risks in industrial environments.

---

## ✅ Our Solution: AEGIS

AEGIS behaves like an **autonomous watchdog** — a non-intrusive, intelligent validator that continuously monitors parameters like temperature, pressure, RPM, and more. If anything deviates from normal behavior, AEGIS immediately flags it, even if the primary controller is compromised.

---

## 🧠 How it Works

- **Phase 1**: Collect real-time sensor data from IoT devices.
- **Phase 2**: Process and normalize data through our ML pipeline.
- **Phase 3**: Anomaly detection using models like Isolation Forest / AutoEncoder.
- **Phase 4**: Log anomalies, alert the user, and suggest mitigation.

---

## ⚙️ Tech Stack

| Layer            | Tools Used                               |
|------------------|-------------------------------------------|
| Frontend         | HTML, CSS, JavaScript                     |
| Backend          | Python (Flask)                            |
| ML Models        | scikit-learn, Pandas, NumPy               |
| Realtime Logging | CSV, Log Files                            |
| UI Framework     | Bootstrap                                 |
| Database         | PostgreSQL                                |
| Deployment       | GitHub, (optional: Vercel / Railway)      |

---

## 🎯 Unique Selling Points

- **Independent** from the control logic of SIIoT devices.
- **Model-agnostic** anomaly detection pipeline.
- **Real-time alerts** on suspected tampering or silent failures.
- **User-friendly UI** for tracking logs and device status.

---

## 💡 Real-World Use Case

Imagine a factory where a malware-infected sensor starts feeding fake RPM data to a robotic arm. AEGIS spots the deviation in pattern and alerts the supervisor — preventing a potential production disaster.

---

## 🚀 Getting Started

```bash
git clone https://github.com/YOUR_USERNAME/aegis.git
cd aegis
pip install -r requirements.txt
python app.py
