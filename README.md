# Edge Object Detector

One model (MediaPipe EfficientDet-Lite0, int8, ~4 MB) running fully on-device:

- `index.html` – web app for **any phone** (iPhone Safari, Android Chrome) and the Pi's browser
- `pi_detect.py` – native Python version for the **Raspberry Pi** (Pi Camera or USB webcam)

It recognizes 80 everyday objects (people, cups, phones, chairs, cars, dogs, and so on). Video never leaves the device; only the model and library are downloaded once.

---

## Part 1 – Phone (iPhone + Android)

Phone browsers only allow camera access on **HTTPS** pages, so host `index.html` somewhere with HTTPS. Easiest free options:

**Option A – Netlify Drop (2 minutes, no account needed to try)**
1. On a computer, go to https://app.netlify.com/drop
2. Drag the folder containing `index.html` onto the page.
3. Open the `https://….netlify.app` link on both phones and tap **Start camera**.

**Option B – GitHub Pages (permanent)**
1. Create a public GitHub repo and upload `index.html`.
2. Settings → Pages → Deploy from branch → `main` / root.
3. Open `https://<username>.github.io/<repo>/` on your phones.

Tips
- iPhone: if the camera doesn't start, check Settings → Safari → Camera → Allow.
- The top bar shows GPU/CPU, frames per second, and milliseconds per frame. Compare your two phones.
- Use the slider to filter out low-confidence detections, and **Flip camera** for the selfie camera.

---

## Part 2 – Raspberry Pi

Hardware: Pi 4 or Pi 5 (4 GB+ recommended), 64-bit Raspberry Pi OS, and a Pi Camera Module or USB webcam.

### Option 1 – Same web app in the Pi's browser (zero code changes)
```bash
cd edge-ai-detector
python3 -m http.server 8000
```
Open **Chromium on the Pi itself** at `http://localhost:8000` (localhost counts as secure, so the camera works).
Note: Chromium sees USB webcams directly. A Pi Camera Module may not appear in the browser, so use Option 2 for that.

### Option 2 – Native Python (faster, works headless over SSH)
```bash
sudo apt update
sudo apt install -y python3-picamera2 python3-opencv   # picamera2 only needed for the Pi Camera Module

python3 -m venv --system-site-packages ~/edge-ai
source ~/edge-ai/bin/activate
pip install mediapipe

cd edge-ai-detector
python pi_detect.py              # window with boxes (needs a desktop/monitor)
python pi_detect.py --headless   # prints detections, good over SSH
```
The model downloads automatically on first run.

Expect roughly 8–15 fps on a Pi 5 and 4–8 fps on a Pi 4 at 640×480.

### Troubleshooting
- **`pip install mediapipe` finds no matching version**: your OS Python may be newer than MediaPipe supports. Create the venv with an older Python, e.g. install `uv` then `uv venv --python 3.12 --system-site-packages ~/edge-ai`.
- **No camera found**: run `rpicam-hello` to test a Pi Camera, or `ls /dev/video*` for a USB webcam. Force one with `--camera pi` or `--camera usb`.
- **Window doesn't open over SSH**: use `--headless`.

---

## Next steps
- Swap the model: try `efficientdet_lite2` for better accuracy (slower), or train your own objects with MediaPipe Model Maker.
- Act on detections: on the Pi, trigger a GPIO LED or buzzer when a "person" appears.
- Speed up the Pi with an AI accelerator (Raspberry Pi AI Kit / Hailo, or Coral USB).
