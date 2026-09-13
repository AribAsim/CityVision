import cv2
import numpy as np
from pathlib import Path

def generate_evidence(output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create a dark gray background
    img = np.ones((480, 640, 3), dtype=np.uint8) * 40
    
    # Draw a simulated road texture
    for _ in range(1000):
        x = np.random.randint(0, 640)
        y = np.random.randint(0, 480)
        color = np.random.randint(20, 60)
        cv2.circle(img, (x, y), 1, (color, color, color), -1)
    
    # Draw bounding box for pothole
    x1, y1, x2, y2 = 200, 150, 440, 330
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
    
    # Add label
    label = "Pothole 87%"
    cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Add watermark
    cv2.putText(img, "SIH26124 DEMO - SYNTHETIC EVIDENCE", (10, 460), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
                
    cv2.imwrite(str(output_path), img, [cv2.IMWRITE_JPEG_QUALITY, 85])
    print(f"Generated synthetic evidence at {output_path}")

if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "data" / "evidence" / "demo_pothole.jpg"
    generate_evidence(out)
