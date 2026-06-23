"""Frame capture — opencv for laptop dev, picamera2 for Pi."""
import base64
import io
import os

from PIL import Image

_USE_PI_CAMERA = os.environ.get("USE_PI_CAMERA", "0") == "1"


def _capture_opencv() -> Image.Image:
    import cv2
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError("Webcam capture failed")
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return Image.fromarray(frame_rgb)


def _capture_picamera2() -> Image.Image:
    from picamera2 import Picamera2
    cam = Picamera2()
    cam.start()
    frame = cam.capture_array()
    cam.stop()
    return Image.fromarray(frame)


def capture_frame() -> Image.Image:
    """Return a PIL Image from the active camera."""
    if _USE_PI_CAMERA:
        return _capture_picamera2()
    return _capture_opencv()


def frame_to_base64(image: Image.Image, max_size: int = 768) -> str:
    """Resize + encode frame as base64 JPEG string."""
    image.thumbnail((max_size, max_size), Image.LANCZOS)
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=85)
    return base64.standard_b64encode(buf.getvalue()).decode()
