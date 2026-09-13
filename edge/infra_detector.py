"""
edge/infra_detector.py
-----------------------
Wrapper for traffic sign and road infrastructure perception model.
Detects road regulatory and warning signs from the bus forward camera.
"""
from __future__ import annotations

import dataclasses
import os
from pathlib import Path
from typing import List

import numpy as np
from ultralytics import YOLO

_REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INFRA_MODEL_PATH = str(
    _REPO_ROOT
    / "RoadDetectionModel"
    / "TrafficInfraModel_yolov8s"
    / "weights"
    / "best.pt"
)

CONFIDENCE_THRESHOLD = 0.35


@dataclasses.dataclass
class InfraDetection:
    class_id: int
    class_name: str
    confidence: float
    bbox: List[int]  # [x1, y1, x2, y2]


class InfraDetector:
    """
    Wraps YOLO traffic sign model to detect signs and infrastructure elements.
    """

    def __init__(self, model_path: str = DEFAULT_INFRA_MODEL_PATH):
        if not os.path.exists(model_path):
            raise FileNotFoundError(
                f"Infra model not found at {model_path}. "
                "Run python scripts/download_models.py first."
            )
        print(f"[INFRA_DETECTOR] Loading infra model from: {model_path}")
        self._model = YOLO(model_path)
        print(f"[INFRA_DETECTOR] Infra model loaded. Class count: {len(self._model.names)}")

    def detect(self, frame: np.ndarray) -> List[InfraDetection]:
        results = self._model.predict(
            source=frame,
            conf=CONFIDENCE_THRESHOLD,
            verbose=False,
        )

        detections: List[InfraDetection] = []
        for r in results:
            boxes = r.boxes
            if boxes is None or len(boxes) == 0:
                continue
            for box in boxes:
                cls_id = int(box.cls[0].item())
                conf = float(box.conf[0].item())
                xyxy = [int(v) for v in box.xyxy[0].tolist()]
                cls_name = self._model.names.get(cls_id, f"sign_{cls_id}")
                detections.append(
                    InfraDetection(
                        class_id=cls_id,
                        class_name=cls_name,
                        confidence=conf,
                        bbox=xyxy,
                    )
                )
        return detections
