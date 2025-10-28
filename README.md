# PiVision-core

**Modular edge-vision core** for Raspberry Pi: camera capture, MJPEG/HTTP streaming, pluggable inference, and flexible notifications. Powers the PiVision suite (Face, NestWatch).

<p>
  <img alt="status" src="https://img.shields.io/badge/status-alpha-orange" />
  <img alt="python" src="https://img.shields.io/badge/Python-3.10%2B-blue" />
  <img alt="platform" src="https://img.shields.io/badge/Platform-Raspberry%20Pi-1abc9c" />
  <img alt="license" src="https://img.shields.io/badge/License-MIT-black" />
</p>

## Features
- **Camera → Stream**: Zero-copy frames to MJPEG (Flask) or raw frames to subscribers
- **Inference plugins**: drop-in modules implement `BaseModel` (sync or threaded)
- **Notification adapters**: desktop notify, MQTT, webhooks (implement `BaseNotifier`)
- **Config-first**: YAML config for device, transport, model, notifier
- **Headless friendly**: systemd-ready; logs to stdout/JSON

## Architecture
```mermaid
flowchart LR
  Cam[Camera] --> Core[PiVision-core]
  Core -->|MJPEG| HTTP[HTTP Stream]
  Core -->|Frames| Model[Inference Plugin]
  Model -->|Events| Notifier[Notifier Adapter]
