# Repository Audit

## 1. What already works
- YOLOv8 model loading and inference via `ultralytics`.
- Video and image processing pipelines using OpenCV and `supervision`.
- A Streamlit interface (`main.py`) that successfully streams and processes video/images/camera feeds.
- Bounding box and label annotations on detected frames.

## 2. Which trained model should be reused
**Model 1 (Custom YOLOv8m)**: `RoadDetectionModel/RoadModel_yolov8m.pt_rounds120_b9/weights/best.pt`.
It is custom-trained for this exact context, has a solid mAP (0.745 @ 0.5), and detects a comprehensive set of relevant classes for Indian roads.

## 3. How inference currently works
Inference is run frame-by-frame. The frame is passed to `model.predict(frame, conf=THRESHOLD)`. Results are converted into `supervision.Detections` for easy parsing and rendering of bounding boxes and labels.

## 4. What classes the model detects
Model 1 detects: `Heavy-Vehicle`, `Light-Vehicle`, `Pedestrian`, `Crack`, `Crack-Severe`, `Pothole`, `Speed-Bump`.
For the MVP, `Crack`, `Crack-Severe`, and `Pothole` are the critical "anomalies" to report.

## 5. How video processing works
In `main.py`, video is processed frame-by-frame in a `while` loop using `cv2.VideoCapture`. Each processed frame is written out to a temporary file via `cv2.VideoWriter`. In live mode, `streamlit-webrtc` handles the frame callbacks.

## 6. What code can be reused
- `main.py`'s `process_frame()` function (with modifications to extract event data instead of just drawing).
- Model loading utilities.
- The `requirements.txt` environment for the inference node.

## 7. What code should remain untouched
- The `.pt` model weights.
- Training scripts (e.g., `train.ipynb`).
- Dataset preprocessing logic.
- We will not modify the internal AI implementation; YOLOv8 usage remains exactly as is.

## 8. What functionality is missing for the SIH26124 MVP
- **Context Injection**: Simulated GPS tracking, bus ID mapping, and timestamping.
- **Event Throttling**: Logic to prevent sending 30 API requests per second for the same pothole.
- **Network Layer**: Code to POST detected anomalies as JSON payloads to a remote server.
- **Backend Service**: A FastAPI server to receive and store events.
- **Authority Dashboard**: A React app to visualize events.

## 9. Existing dependencies and Python version assumptions
- **Dependencies**: `ultralytics`, `opencv-python`, `supervision`, `torch`, `streamlit`, `streamlit-webrtc`.
- **Python Version**: Likely 3.9+ given the dependencies.

## 10. Any risks or compatibility issues
- **Repository Size/Corruption**: The git repository has large files and encountered packfile corruption on checkout. We cloned a shallow copy (`temp_clone`) to retrieve missing files.
- **Performance**: Running YOLOv8m inference + streaming + network requests might cause lag. Event throttling is strictly required.
