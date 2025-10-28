from flask import Flask, Response
from picamera2 import Picamera2
import io
from PIL import Image
import time

# Initialize Flask app
app = Flask(__name__)

# Initialize PiCamera2
cam = Picamera2()

# Configure camera for video capture
video_config = cam.create_video_configuration(main={"size": (640, 480)})
cam.configure(video_config)

# Start the camera
cam.start()
time.sleep(2)  # Give time for the camera to warm up

def generate_frames():
    while True:
        try:
            # Capture frame
            frame = cam.capture_array()

            # Convert NumPy array to PIL Image
            img = Image.fromarray(frame).rotate(180)

            # Convert RGBA to RGB if needed
            if img.mode == 'RGBA':
                img = img.convert('RGB')

            # Save to buffer as JPEG
            buf = io.BytesIO()
            img.save(buf, format='JPEG')
            jpeg_frame = buf.getvalue()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg_frame + b'\r\n')
        except Exception as e:
            print(f"Error capturing frame: {e}")
            break


@app.route('/')
def index():
    return "<h1>Pi Camera Server</h1><p>Stream available at <a href='/video_feed'>/video_feed</a></p>"

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    # Run Flask app
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)