import os
import time
import cv2
import numpy as np
import face_recognition
from datetime import datetime
from typing import Dict, Optional

# -----------------------------
# CONFIG
# -----------------------------
MATCH_THRESHOLD = 0.55          # lower = stricter; 0.6 is a common default
COOLDOWN_SECONDS = 20           # per-identity cooldown to avoid spam
TAKE_SNAPSHOT_ON_UNKNOWN = True
SNAPSHOT_DIR = "events"

# Notification backends
USE_NOTIFY_SEND = True          # Linux desktop notifications via `notify-send`
USE_MQTT = False                # Set True if you have a broker running
MQTT_HOST = "127.0.0.1"
MQTT_TOPIC = "pivision/events"

# -----------------------------
# Utilities
# -----------------------------
def convert_img(bgr_im):
    """BGR -> RGB uint8"""
    rgb_im = cv2.cvtColor(bgr_im, cv2.COLOR_BGR2RGB)
    return rgb_im.astype("uint8")

def ensure_dir(d):
    os.makedirs(d, exist_ok=True)

def now_iso():
    return datetime.now().isoformat(timespec="seconds")

# -----------------------------
# Notifier
# -----------------------------
class Notifier:
    def __init__(self, use_notify=True, use_mqtt=False, mqtt_host="127.0.0.1", mqtt_topic="pivision/events"):
        self.use_notify = use_notify
        self.use_mqtt = use_mqtt
        self.mqtt = None
        self.topic = mqtt_topic
        if self.use_mqtt:
            try:
                import paho.mqtt.client as mqtt
                self.mqtt = mqtt.Client()
                self.mqtt.connect(mqtt_host)
            except Exception as e:
                print(f"[WARN] MQTT disabled (failed to init): {e}")
                self.use_mqtt = False

    def notify(self, title: str, message: str, payload: Optional[Dict] = None):
        # Print always (debug-friendly)
        print(f"[NOTIFY] {title}: {message} {payload or ''}")

        # Desktop notify (best-effort)
        if self.use_notify:
            try:
                # notify-send <summary> <body>
                import subprocess
                body = message
                if payload:
                    body += f"\n{payload}"
                subprocess.run(["notify-send", title, body], check=False)
            except Exception as e:
                print(f"[WARN] notify-send failed: {e}")

        # MQTT (best-effort)
        if self.use_mqtt and self.mqtt:
            try:
                import json
                msg = {"title": title, "message": message, "time": now_iso()}
                if payload:
                    msg.update(payload)
                self.mqtt.publish(self.topic, json.dumps(msg))
            except Exception as e:
                print(f"[WARN] MQTT publish failed: {e}")

# -----------------------------
# Known faces TODO: Update database handling
# -----------------------------
# Image 1. Sander
sanderimg = cv2.imread("/sander.jpg")  # adjust path
if sanderimg is None:
    raise FileNotFoundError("Could not load /sander.jpg — update the path.")
rgb_sanderim = convert_img(sanderimg)
sander_face_encoding = face_recognition.face_encodings(rgb_sanderim)[0]

encodings_known_faces = [sander_face_encoding]
known_faces_names = ["Sander"]

# -----------------------------
# Runtime
# -----------------------------
if TAKE_SNAPSHOT_ON_UNKNOWN:
    ensure_dir(SNAPSHOT_DIR)

notifier = Notifier(use_notify=USE_NOTIFY_SEND, use_mqtt=USE_MQTT,
                    mqtt_host=MQTT_HOST, mqtt_topic=MQTT_TOPIC)

# Per-identity cooldown tracking
last_notified_at: Dict[str, float] = {}

# Init video capture
video_capture = cv2.VideoCapture(0)
if not video_capture.isOpened():
    raise RuntimeError("Could not open camera index 0")

print("[INFO] Camera opened. Press 'q' to quit.")

try:
    while True:
        ok, frame_bgr = video_capture.read()
        if not ok:
            print("[WARN] Frame grab failed.")
            continue

        # Visualize
        cv2.imshow("Video", frame_bgr)

        rgb_frame = convert_img(frame_bgr)
        if rgb_frame is None or len(rgb_frame.shape) != 3 or rgb_frame.shape[2] != 3:
            print("[WARN] Frame invalid for face recognition.")
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
            continue

        # Detect + encode
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # For each face
        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            # Compute distances to known faces
            distances = face_recognition.face_distance(encodings_known_faces, face_encoding)
            if len(distances) > 0:
                best_idx = int(np.argmin(distances))
                best_dist = float(distances[best_idx])
                is_match = best_dist <= MATCH_THRESHOLD
                name = known_faces_names[best_idx] if is_match else "Unknown"
            else:
                best_dist = 1.0
                is_match = False
                name = "Unknown"

            # Draw box + label
            cv2.rectangle(frame_bgr, (left, top), (right, bottom), (0, 0, 255), 2)
            label = f"{name} ({best_dist:.2f})"
            cv2.rectangle(frame_bgr, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            cv2.putText(frame_bgr, label, (left + 6, bottom - 8), cv2.FONT_HERSHEY_DUPLEX, 0.7, (255, 255, 255), 1)

            # Debounced notification
            now = time.time()
            last = last_notified_at.get(name, 0.0)
            if now - last >= COOLDOWN_SECONDS:
                last_notified_at[name] = now
                # Compose payload
                payload = {
                    "event": "face-detected",
                    "label": name,
                    "distance": round(best_dist, 4),
                    "threshold": MATCH_THRESHOLD,
                    "time": now_iso(),
                }
                title = "Face detected"
                message = f"{name} @ {best_dist:.2f} (≤ {MATCH_THRESHOLD} = match: {is_match})"
                notifier.notify(title, message, payload)

                # Snapshot unknowns
                if TAKE_SNAPSHOT_ON_UNKNOWN and name == "Unknown":
                    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
                    out_path = os.path.join(SNAPSHOT_DIR, f"unknown-{ts}.jpg")
                    # Crop face region safely
                    t, b = max(top, 0), max(bottom, 0)
                    l, r = max(left, 0), max(right, 0)
                    crop = frame_bgr[t:b, l:r]
                    if crop.size > 0:
                        cv2.imwrite(out_path, crop)
                    else:
                        # fallback: save full frame
                        cv2.imwrite(out_path, frame_bgr)
                    print(f"[INFO] Saved snapshot: {out_path}")

        # Show annotated frame
        cv2.imshow("Video", frame_bgr)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

finally:
    video_capture.release()
    cv2.destroyAllWindows()
