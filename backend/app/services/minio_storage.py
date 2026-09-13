"""
backend/app/services/minio_storage.py
--------------------------------------
Evidence storage service with fallback:
- If MINIO_ENABLED=true: uploads snapshot to MinIO S3 bucket and returns public URL.
- If MINIO_ENABLED=false (default): falls back to local disk storage in data/evidence/.
"""
import os
import io
from pathlib import Path
from typing import Optional, Union, Tuple
import cv2
import numpy as np

MINIO_ENABLED = os.getenv("MINIO_ENABLED", "false").lower() == "true"
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_SECURE = os.getenv("MINIO_SECURE", "false").lower() == "true"
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "cityvision-evidence")

LOCAL_EVIDENCE_DIR = Path(__file__).resolve().parents[3] / "data" / "evidence"
LOCAL_EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

_client = None


def get_minio_client():
    global _client
    if not MINIO_ENABLED:
        return None
    if _client is None:
        try:
            from minio import Minio
            _client = Minio(
                MINIO_ENDPOINT,
                access_key=MINIO_ACCESS_KEY,
                secret_key=MINIO_SECRET_KEY,
                secure=MINIO_SECURE,
            )
            # Ensure bucket exists
            if not _client.bucket_exists(MINIO_BUCKET):
                _client.make_bucket(MINIO_BUCKET)
        except Exception as e:
            print(f"[STORAGE] MinIO client initialization failed ({e}). Falling back to local disk.")
            return None
    return _client


def save_evidence_image(
    image_data: Union[np.ndarray, bytes],
    filename: str,
    content_type: str = "image/jpeg",
) -> Tuple[str, str]:
    """
    Save image either to MinIO S3 or local disk.
    
    Args:
        image_data: OpenCV image (np.ndarray) or raw bytes.
        filename: Destination filename (e.g., 'Pothole_123456789.jpg').
        content_type: MIME type of the image.

    Returns:
        Tuple[str, str]: (storage_type, resource_path_or_url)
            storage_type: "minio" or "local"
            resource_path_or_url: MinIO object key/URL or local file path string
    """
    # Convert numpy array to JPEG bytes if necessary
    if isinstance(image_data, np.ndarray):
        success, encoded = cv2.imencode(".jpg", image_data, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not success:
            raise ValueError("Failed to encode image to JPEG")
        raw_bytes = encoded.tobytes()
    else:
        raw_bytes = image_data

    client = get_minio_client()
    if client:
        try:
            client.put_object(
                bucket_name=MINIO_BUCKET,
                object_name=filename,
                data=io.BytesIO(raw_bytes),
                length=len(raw_bytes),
                content_type=content_type,
            )
            protocol = "https" if MINIO_SECURE else "http"
            url = f"{protocol}://{MINIO_ENDPOINT}/{MINIO_BUCKET}/{filename}"
            return "minio", url
        except Exception as exc:
            print(f"[STORAGE] MinIO put_object failed ({exc}). Falling back to local disk.")

    # Local fallback
    local_path = LOCAL_EVIDENCE_DIR / filename
    with open(local_path, "wb") as f:
        f.write(raw_bytes)
    return "local", str(local_path)
