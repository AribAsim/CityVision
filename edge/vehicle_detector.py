"""
edge/vehicle_detector.py
-------------------------
Wrapper for base YOLOv8n focusing exclusively on vehicle and pedestrian classes.
Used in Phase 2 perception and Phase 3 traffic density / near-miss safety analytics.
"""
from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from typing import List

import numpy as np
from ultralytics import YOLO

# COCO vehicle and vulnerable road user (VRU) class indices
# 0: person, 1: bicycle, 2: car, 3: motorcycle, 5: bus, 7: truck
TARGET_COCO_CLASSES = {
    0: "person",
    1: "bicycle",
    2: "car",
    3: "motorcycle",
    5: "bus",
    7: "truck",
}

_REPO_ROOT = Path(__file__).resolve().parents[1]
_LOCAL_MODEL = _REPO_ROOT / "yolov8n.pt"
DEFAULT_VEHICLE_MODEL = str(_LOCAL_MODEL) if _LOCAL_MODEL.exists() else "yolov8n.pt"
CONFIDENCE_THRESHOLD = 0.35


@dataclasses.dataclass
class VehicleDetection:
    class_id: int
    class_name: str
    confidence: float
    bbox: List[int]  # [x1, y1, x2, y2]


class VehicleDetector:
    """
    Wraps standard YOLOv8n to extract vehicle and VRU bounding boxes.
    """

    def __init__(self, model_path: str = DEFAULT_VEHICLE_MODEL):
        print(f"[VEHICLE_DETECTOR] Loading model from: {model_path}")
        self._model = YOLO(model_path)
        print(f"[VEHICLE_DETECTOR] Model ready. Tracking classes: {list(TARGET_COCO_CLASSES.values())}")

    def detect(self, frame: np.ndarray) -> List[VehicleDetection]:
        results = self._model.predict(
            source=frame,
            conf=CONFIDENCE_THRESHOLD,
            classes=list(TARGET_COCO_CLASSES.keys()),
            verbose=False,
        )

        detections: List[VehicleDetection] = []
        for r in results:
            boxes = r.boxes
            if boxes is None or len(boxes) == 0:
                continue
            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                xyxy = [int(v) for v in box.xyxy[0].tolist()]
                cls_name = TARGET_COCO_CLASSES.get(cls_id, self._model.names.get(cls_id, "unknown"))
                detections.append(
                    VehicleDetection(
                        class_id=cls_id,
                        class_name=cls_name,
                        confidence=conf,
                        bbox=xyxy,
                    )
                )
        return detections
