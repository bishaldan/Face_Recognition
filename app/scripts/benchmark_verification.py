import argparse
import json
import time
from pathlib import Path

from app.core.config import get_settings
from app.services.recognition.engines import FaceRecognitionPipeline


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark image processing latency for the recognition pipeline.")
    parser.add_argument(
        "--images",
        nargs="+",
        required=True,
        help="One or more image paths to run through the pipeline.",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Number of timed runs per image.",
    )
    parser.add_argument(
        "--output",
        default="reports/benchmark_report.json",
        help="Where to write benchmark results.",
    )
    args = parser.parse_args()

    settings = get_settings()
    pipeline = FaceRecognitionPipeline(settings)
    threshold = settings.default_similarity_threshold
    results = []

    for image_path_str in args.images:
        image_path = Path(image_path_str)
        image_bytes = image_path.read_bytes()

        warmup_start = time.perf_counter()
        warmup = pipeline.process_image(image_bytes, threshold)
        warmup_ms = round((time.perf_counter() - warmup_start) * 1000, 2)

        timed_runs_ms = []
        for _ in range(args.runs):
            started = time.perf_counter()
            pipeline.process_image(image_bytes, threshold)
            timed_runs_ms.append(round((time.perf_counter() - started) * 1000, 2))

        results.append(
            {
                "image": str(image_path),
                "warmup_ms": warmup_ms,
                "mean_ms": round(sum(timed_runs_ms) / len(timed_runs_ms), 2),
                "min_ms": min(timed_runs_ms),
                "max_ms": max(timed_runs_ms),
                "runs": timed_runs_ms,
                "status": warmup.status,
                "reason_codes": warmup.reason_codes,
            }
        )

    payload = {
        "backend": pipeline.backend_name,
        "model": pipeline.model_name,
        "threshold": threshold,
        "results": results,
    }
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2))
    print(json.dumps(payload, indent=2))
    print(f"Wrote benchmark report to {output_path}")


if __name__ == "__main__":
    main()

