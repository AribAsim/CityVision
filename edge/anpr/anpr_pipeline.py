"""
edge/anpr/anpr_pipeline.py
---------------------------
Full ANPR pipeline combining PlateDetector and OCREngine.
"""
from __future__ import annotations

import dataclasses
from typing import List, Optional
import numpy as np

from edge.anpr.plate_detector import PlateDetector, PlateBBox
from edge.anpr.ocr_engine import OCREngine


@dataclasses.dataclass
class PlateReadResult:
    plate_text: str
    plate_confidence: float
    ocr_confidence: float
    bbox: List[int]
    crop: np.ndarray


class ANPRPipeline:
    """
    Localizes license plates and executes OCR extraction.
    """

    def __init__(
        self,
        plate_detector: Optional[PlateDetector] = None,
        ocr_engine: Optional[OCREngine] = None,
    ):
        self.detector = plate_detector or PlateDetector()
        self.ocr = ocr_engine or OCREngine()

    def process_frame(self, frame: np.ndarray) -> List[PlateReadResult]:
        plate_boxes = self.detector.detect_plates(frame)
        results: List[PlateReadResult] = []

        for p in plate_boxes:
            text, ocr_conf = self.ocr.recognize(p.crop)
            if len(text) >= 4:  # Minimum valid plate characters
                results.append(
                    PlateReadResult(
                        plate_text=text,
                        plate_confidence=p.confidence,
                        ocr_confidence=ocr_conf,
                        bbox=p.bbox,
                        crop=p.crop,
                    )
                )
        return results
