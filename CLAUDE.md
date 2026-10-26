# Edge Object Detector – project context

## Goal
A simple, device-agnostic Edge AI app: real-time object detection that runs fully on-device.
Phase 1: phones (iPhone + Android) via a web page. Phase 2: Raspberry Pi.
The same model is used everywhere: MediaPipe EfficientDet-Lite0 (int8, ~4 MB, 80 COCO classes).

## Files
- `index.html` – the whole web app (single file, no build step). Uses MediaPipe Tasks Vision
  `@mediapipe/tasks-vision@0.10.14`, imported from jsDelivr as `vision_bundle.mjs`; WASM from the
  same package's `/wasm`; model from `storage.googleapis.com/mediapipe-models/...`.
  Features: Start/Stop, Pause/Resume (freeze frame), Flip camera, GPU/CPU switch, confidence slider,
  live results strip (chips like "person ×2 · 91%"), top bar with fps / ms / object count.
  Version tag in the header (currently **v5**) – bump it on every change so the user can confirm
  which copy their phone loaded.
- `pi_detect.py` – native Python version for Raspberry Pi (MediaPipe Python Tasks API, VIDEO mode).
  Camera: picamera2 (Pi Camera Module) with OpenCV USB-webcam fallback. `--headless`, `--camera`,
  `--threshold`, `--max-results`. Downloads the model on first run. Not yet tested on hardware.
- `README.md` – user-facing setup steps for phone hosting and the Pi.

## Hosting
Deployed on GitHub Pages from the `main` branch, root folder:
`https://narasimhulu-pathi.github.io/<repo-name>/`. HTTPS is required for camera access on phones.
GitHub Pages caches for up to ~10 minutes after an upload.

## History and known issues
1. v1 gated detection on `video.currentTime` changing – detection never ran on the user's phone.
   Fixed in v3: run detection every animation frame with strictly increasing timestamps.
2. **GPU on iOS Safari is disabled (v9).** Root cause fully traced: (a) int8 model + WebGL GPU
   delegate returns 0 detections silently (int8 ops unsupported on WebGL); (b) float32 model loads
   and runs but iOS Safari uses float16 precision internally in WebGL shaders, corrupting outputs
   (wrong labels, misaligned boxes, missed detections). WebGL2 and EXT_color_buffer_float are both
   present on the device — the constraint is shader precision, not extension support. CPU (WASM
   float32) is accurate and fast on A-series chips. GPU button is greyed out on iOS with a tooltip.
3. v4 added a safety-net classic script that shows an on-screen error if the module fails to load.
4. ~~**Open issue:** in v4 the results strip under the camera stayed on the placeholder
   "Detected objects will be listed here." even while boxes were being drawn.~~ **Fixed in v5.**
   Results strip confirmed working on the user's phone (2026-10-25).

## Next steps
- Confirm v5 results strip works on Android (Chrome) — iPhone confirmed 2026-10-25.
- GPU on iOS Safari fully investigated and resolved (v9) — disabled with explanation.
- Move to the Raspberry Pi: run `pi_detect.py` (see README), then optionally the web app in
  Chromium at `http://localhost:8000`.
- Ideas: GPIO action on "person" detected, larger model (efficientdet_lite2), custom training
  with MediaPipe Model Maker, Hailo/Coral accelerator.

## Working notes
- Keep `index.html` a single self-contained file (the user uploads it to GitHub by hand, often from a phone).
- No real camera is available in a dev sandbox – test logic with a stubbed detector, and ask the
  user for screenshots from the phone.
