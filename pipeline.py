from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path

import cv2
import pandas as pd
from ultralytics import YOLO


DEFAULT_MODEL = "yolov8n.pt"


def run_pipeline(
    video_path: str | Path,
    output_video_path: str | Path,
    metrics_path: str | Path,
    model_name: str = DEFAULT_MODEL,
    sample_every: int = 1,
    confidence: float = 0.35,
) -> None:
    """Detect and track people on a video, then save annotated video and per-frame metrics."""
    video_path = Path(video_path)
    output_video_path = Path(output_video_path)
    metrics_path = Path(metrics_path)
    output_video_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.parent.mkdir(parents=True, exist_ok=True)

    if not video_path.exists():
        raise FileNotFoundError(f"Input video not found: {video_path}")

    model = YOLO(model_name)
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    if width <= 0 or height <= 0:
        raise RuntimeError("Could not read video dimensions")

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(output_video_path), fourcc, fps, (width, height))

    metrics_data: list[dict[str, object]] = []
    frame_count = 0
    processed_count = 0

    print("Starting person detection and tracking...")
    try:
        while cap.isOpened():
            success, frame = cap.read()
            if not success:
                break

            if frame_count % sample_every != 0:
                frame_count += 1
                continue

            results = model.track(
                frame,
                persist=True,
                classes=[0],  # COCO class 0 = person
                conf=confidence,
                verbose=False,
            )

            boxes = results[0].boxes
            people_count = len(boxes.id.tolist()) if boxes.id is not None else 0
            detection_count = len(boxes) if boxes is not None else 0

            timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
            metrics_data.append(
                {
                    "timestamp_utc": timestamp,
                    "frame": frame_count,
                    "second": round(frame_count / fps, 2),
                    "people_count": people_count,
                    "detections": detection_count,
                }
            )

            annotated_frame = results[0].plot()
            out.write(annotated_frame)
            frame_count += 1
            processed_count += 1
    finally:
        cap.release()
        out.release()

    df = pd.DataFrame(metrics_data)
    df.to_csv(metrics_path, index=False)
    print(
        f"Pipeline completed: processed_frames={processed_count}, "
        f"metrics={metrics_path}, annotated_video={output_video_path}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="585 Золото CV Retail MVP pipeline")
    parser.add_argument("--input", default="data/input.mp4", help="Path to input mp4/video file")
    parser.add_argument("--output-video", default="output/output_annotated.mp4", help="Annotated output video path")
    parser.add_argument("--metrics", default="output/retail_metrics.csv", help="CSV metrics output path")
    parser.add_argument("--model", default=DEFAULT_MODEL, help="YOLO model name/path")
    parser.add_argument("--sample-every", type=int, default=1, help="Process every Nth frame")
    parser.add_argument("--confidence", type=float, default=0.35, help="Detection confidence threshold")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(
        video_path=args.input,
        output_video_path=args.output_video,
        metrics_path=args.metrics,
        model_name=args.model,
        sample_every=max(1, args.sample_every),
        confidence=args.confidence,
    )
