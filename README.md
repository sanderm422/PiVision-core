# PiVision

Smart, low-power **facial recognition and alerting system**
Runs on Raspberry Pi with local recognition, visual annotations, and flexible notifications (desktop or MQTT).

<p>
  <img alt="status" src="https://img.shields.io/badge/status-beta-green" />
  <img alt="python" src="https://img.shields.io/badge/Python-3.10%2B-blue" />
  <img alt="platform" src="https://img.shields.io/badge/Platform-Raspberry%20Pi_4%2FZero_W-1abc9c" />
  <img alt="license" src="https://img.shields.io/badge/License-MIT-black" />
</p>

---

##  Highlights

-   Real-time **face recognition** using `face_recognition` + `dlib`
-   **Notifications** via `notify-send` or MQTT (configurable)
-   Reusable inference logic compatible with **PiVision-core**
-   Cooldown & distance-based scoring (no spam, more signal)
-   Automatic **snapshots of unknown faces**
-   Designed as a **drop-in plugin** for the PiVision ecosystem

---

##  Architecture

```mermaid
flowchart LR
  Cam[Camera / USB / CSI] --> Core[PiVision-core]
  Core -->|Frame| FaceModel[PiVision-face Model]
  FaceModel -->|Events| Notifier[Notifier (MQTT/Desktop)]
  Notifier --> User((User Alerts))
  FaceModel -->|Snapshots| Disk[(events/ folder)]
