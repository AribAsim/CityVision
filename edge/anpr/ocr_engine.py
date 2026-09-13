"""
edge/anpr/ocr_engine.py
------------------------
EasyOCR-based license plate text recognizer.
Includes pre-processing (grayscale, thresholding) and Indian registration formatting.
"""
from __future__ import annotations

import re
from typing import Optional, Tuple
import cv2
import numpy as np

# Standard Indian License Plate regex pattern (e.g., DL01AB1234, MH12DE1433, HR26DQ5551)
INDIAN_PLATE_REGEX = re.compile(r"^[A-Z]{2}[0-9]{1,2}[A-Z]{1,3}[0-9]{4}$")


class OCREngine:
    """
    Lightweight OCR wrapper using EasyOCR.
    """

    def __init__(self, languages: list[str] = None):
        if languages is None:
            languages = ["en"]
        print("[ANPR] Initialising EasyOCR reader (CPU mode)...")
        import easyocr
        self._reader = easyocr.Reader(languages, gpu=False)
        print("[ANPR] EasyOCR ready.")

    def recognize(self, plate_crop: np.ndarray) -> Tuple[str, float]:
        """
        Run OCR on cropped plate snippet.
        Returns cleaned text string and OCR confidence score.
        """
        if plate_crop is None or plate_crop.size == 0:
            return "", 0.0

        # Pre-process: convert to gray and resize if small
        h, w = plate_crop.shape[:2]
        if h < 32 or w < 96:
            scale = max(32 / max(h, 1), 96 / max(w, 1))
            plate_crop = cv2.resize(plate_crop, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)

        gray = cv2.cvtColor(plate_crop, cv2.COLOR_BGR2GRAY)
        # Contrast adjustment
        gray = cv2.equalizeHist(gray)

        try:
            results = self._reader.readtext(gray)
        except Exception as e:
            return "", 0.0

        if not results:
            return "", 0.0

        # Combine text segments sorted by left-to-right
        sorted_results = sorted(results, key=lambda x: x[0][0][0])
        raw_text = "".join(res[1] for res in sorted_results)
        conf = float(np.mean([res[2] for res in sorted_results]))

        # Clean alphanumeric characters only
        clean_text = re.sub(r"[^A-Za-z0-9]", "", raw_text).upper()

        return clean_text, conf
