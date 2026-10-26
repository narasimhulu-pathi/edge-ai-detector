#!/usr/bin/env python3
"""
Edge object detector for Raspberry Pi (also runs on any Linux/Mac/Windows PC).

Uses the same MediaPipe EfficientDet-Lite0 model as the phone web app (index.html).
Works with a Raspberry Pi Camera Module (via picamera2) or any USB webcam (via OpenCV).

Usage:
    python pi_detect.py                 # show a window with boxes
    python pi_detect.py --headless      # no display, print detections (SSH-friendly)
    python pi_detect.py --camera usb    # force USB webcam
    python pi_detect.py --threshold 0.4
"""
import argparse
import os
import time
import urllib.request

import cv2
import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision

MODEL_URL = ("https://storage.googleapis.com/mediapipe-models/object_detector/"
             "efficientdet_lite0/int8/1/efficientdet_lite0.tflite")
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "efficientdet_lite0.tflite")


def ensure_model():
    if not os.path.exists(MODEL_PATH):
        print("Downloading model (about 4 MB)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    return MODEL_PATH


class Camera:
    """Returns RGB frames from a Pi Camera Module or a USB webcam."""

    def __init__(self, kind="auto", width=640, height=480):
        self.picam = None
        self.cap = None
        if kind in ("auto", "pi"):
            try:
                from picamera2 import Picamera2
                self.picam = Picamera2()
                cfg = self.picam.create_preview_configuration(
                    main={"size": (width, height), "format": "RGB888"})
                self.picam.configure(cfg)
                self.picam.start()
                time.sleep(1)  # let exposure settle
                print("Using Pi Camera Module")
                return
            except Exception as e:
                if kind == "pi":
                    raise RuntimeError(f"Pi camera not available: {e}")
                self.picam = None
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        if not self.cap.isOpened():
            raise RuntimeError("No camera found. Plug in a USB webcam or connect a Pi Camera Module.")
        print("Using USB webcam")

    def read_rgb(self):
        if self.picam:
            # Picamera2's "RGB888" is actually BGR byte order, so convert to RGB
            return cv2.cvtColor(self.picam.capture_array(), cv2.COLOR_BGR2RGB)
        ok, frame = self.cap.read()
        if not ok:
            return None
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def close(self):
        if self.picam:
            self.picam.stop()
        if self.cap:
            self.cap.release()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--camera", choices=["auto", "pi", "usb"], default="auto")
    ap.add_argument("--threshold", type=float, default=0.5)
    ap.add_argument("--max-results", type=int, default=5)
    ap.add_argument("--headless", action="store_true", help="no window; print detections")
    args = ap.parse_args()

    options = vision.ObjectDetectorOptions(
        base_options=mp_python.BaseOptions(model_asset_path=ensure_model()),
        running_mode=vision.RunningMode.VIDEO,
        score_threshold=args.threshold,
        max_results=args.max_results,
    )
    detector = vision.ObjectDetector.create_from_options(options)
    cam = Camera(args.camera)

    t_start = time.monotonic()
    frames, fps_t0, fps = 0, time.monotonic(), 0.0
    try:
        while True:
            rgb = cam.read_rgb()
            if rgb is None:
                continue
            ts_ms = int((time.monotonic() - t_start) * 1000)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result = detector.detect_for_video(mp_image, ts_ms)

            frames += 1
            now = time.monotonic()
            if now - fps_t0 >= 1.0:
                fps = frames / (now - fps_t0)
                frames, fps_t0 = 0, now

            labels = [f"{d.categories[0].category_name} {d.categories[0].score:.0%}"
                      for d in result.detections]

            if args.headless:
                if labels:
                    print(f"[{fps:4.1f} fps] " + ", ".join(labels))
                continue

            bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
            for d, label in zip(result.detections, labels):
                b = d.bounding_box
                x, y, w, h = b.origin_x, b.origin_y, b.width, b.height
                cv2.rectangle(bgr, (x, y), (x + w, y + h), (165, 200, 62), 2)
                cv2.putText(bgr, label, (x + 4, max(18, y - 6)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (165, 200, 62), 2)
            cv2.putText(bgr, f"{fps:.1f} fps", (10, 24),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.imshow("Edge Object Detector (q to quit)", bgr)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    except KeyboardInterrupt:
        pass
    finally:
        cam.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
