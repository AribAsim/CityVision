"""
scripts/inspect_merges.py
Inspects track merges at thresholds 0.80, 0.85, 0.90, 0.95
Checks our 4 confirmed fragment pairs:
1. Track 4 (F61-84) & Track 6 (F94-185)
2. Track 6 (F94-185) & Track 10 (F163-205)
3. Track 12 (F200-259) & Track 17 (F249-254)
4. Track 14 (F227-239) & Track 16 (F241-296)
And verifies distinct potholes (e.g. 3, 7, 8, 9, 11, 21, 22, 25, 31, 33, 35, 36)
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pickle
import numpy as np
from edge.detector import RawDetection
from edge.anomaly_tracker import AnomalyTracker

with open("scratch/yolo_detections_cache.pkl", "rb") as f:
    frames_dets = pickle.load(f)

for th in [0.80, 0.85, 0.90, 0.95]:
    tracker = AnomalyTracker(minimum_matching_threshold=th)
    tracks = []
    dummy = np.zeros((10, 10, 3), dtype=np.uint8)
    for i, fd in enumerate(frames_dets):
        tracks.extend(tracker.update([RawDetection(c, conf, b) for c, conf, b in fd], dummy, None, i))
    tracks.extend(tracker.flush())
    
    potholes = sorted([t for t in tracks if t.class_name == "Pothole"], key=lambda x: x.first_frame_idx)
    print(f"\n{'='*75}")
    print(f"THRESHOLD: {th:.2f} | Total: {len(tracks)} | Potholes: {len(potholes)}")
    print(f"{'='*75}")
    for p in potholes:
        print(f"  Trk {p.track_id:2d} | F{p.first_frame_idx:3d} -> F{p.last_frame_idx:3d} (span={p.last_frame_idx - p.first_frame_idx:3d}, hits={p.hit_count:2d}, conf={p.best_confidence:.2f}) | bbox={p.best_bbox}")
