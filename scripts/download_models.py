"""
scripts/download_models.py
--------------------------
Downloads required pre-trained YOLO models for Phase 2:
1. yolov8n.pt (COCO vehicle and pedestrian detector) -> auto via ultralytics
2. traffic-signs.pt (Traffic Sign / Infra detector) -> downloaded to RoadDetectionModel/TrafficInfraModel_yolov8/weights/best.pt
3. no_plate_model.pt (Indian License Plate detector) -> downloaded to RoadDetectionModel/ANPRPlateDetector_yolov8n/weights/best.pt
"""
import os
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

MODELS = [
    {
        "name": "Traffic Sign Detection (JakobJFL)",
        "url": "https://huggingface.co/JakobJFL/yolov8-dk-Traffic-Signs/resolve/main/weights/best.pt",
        "target": REPO_ROOT / "RoadDetectionModel" / "TrafficInfraModel_yolov8s" / "weights" / "best.pt",
    },
    {
        "name": "Indian License Plate Detection (gursharn01)",
        "url": "https://huggingface.co/gursharn01/indian-license-plate-detector/resolve/main/no_plate_model.pt",
        "target": REPO_ROOT / "RoadDetectionModel" / "ANPRPlateDetector_yolov8n" / "weights" / "best.pt",
    },
]


def download_all():
    # 1. Base YOLOv8n (COCO)
    print("[DOWNLOAD] Ensuring base YOLOv8n is cached...")
    from ultralytics import YOLO
    _ = YOLO("yolov8n.pt")
    print("[DOWNLOAD] ✓ YOLOv8n ready.")

    # 2. Additional models
    for m in MODELS:
        target_path: Path = m["target"]
        target_path.parent.mkdir(parents=True, exist_ok=True)
        if target_path.exists() and target_path.stat().st_size > 100_000:
            print(f"[DOWNLOAD] ✓ {m['name']} already exists at {target_path.name}")
            continue

        print(f"[DOWNLOAD] Fetching {m['name']} from {m['url']} ...")
        try:
            req = urllib.request.Request(m["url"], headers={"User-Agent": "CityVision-ModelDownloader/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp, open(target_path, "wb") as out_file:
                out_file.write(resp.read())
            print(f"[DOWNLOAD] ✓ Saved to {target_path} ({target_path.stat().st_size} bytes)")
        except Exception as e:
            print(f"[DOWNLOAD] ✗ Failed downloading {m['name']}: {e}")

    print("\n[DOWNLOAD] All Phase 2 models checked!")


if __name__ == "__main__":
    download_all()
