import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.core.config import get_settings
from app.services.recognition.engines import FaceRecognitionPipeline, cosine_similarity


@dataclass(slots=True)
class PairResult:
    left_image: str
    right_image: str
    same_person: bool
    similarity: float
    accepted: bool
    threshold: float


def load_manifest(path: Path) -> list[dict]:
    return json.loads(path.read_text())


def embed_image(pipeline: FaceRecognitionPipeline, image_path: Path, threshold: float) -> list[float]:
    result = pipeline.process_image(image_path.read_bytes(), threshold)
    if result.embedding is None:
        raise ValueError(
            f"Could not generate embedding for {image_path}. Reason codes: {result.reason_codes}"
        )
    return result.embedding


def evaluate_pairs(manifest: list[dict], threshold: float) -> tuple[list[PairResult], dict]:
    settings = get_settings()
    pipeline = FaceRecognitionPipeline(settings)
    rows: list[PairResult] = []

    true_positive = true_negative = false_positive = false_negative = 0
    for item in manifest:
        left = Path(item["left_image"])
        right = Path(item["right_image"])
        same_person = bool(item["same_person"])

        left_embedding = embed_image(pipeline, left, threshold)
        right_embedding = embed_image(pipeline, right, threshold)
        similarity = cosine_similarity(left_embedding, right_embedding)
        accepted = similarity >= threshold

        if same_person and accepted:
            true_positive += 1
        elif same_person and not accepted:
            false_negative += 1
        elif not same_person and accepted:
            false_positive += 1
        else:
            true_negative += 1

        rows.append(
            PairResult(
                left_image=str(left),
                right_image=str(right),
                same_person=same_person,
                similarity=round(similarity, 4),
                accepted=accepted,
                threshold=threshold,
            )
        )

    total = max(len(rows), 1)
    summary = {
        "threshold": threshold,
        "backend": pipeline.backend_name,
        "model": pipeline.model_name,
        "pairs_evaluated": len(rows),
        "accuracy": round((true_positive + true_negative) / total, 4),
        "true_positive": true_positive,
        "true_negative": true_negative,
        "false_positive": false_positive,
        "false_negative": false_negative,
    }
    return rows, summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate face pair similarity against a manifest.")
    parser.add_argument("--manifest", required=True, help="Path to a JSON manifest of labeled image pairs.")
    parser.add_argument(
        "--threshold",
        type=float,
        default=None,
        help="Similarity threshold override. Defaults to the configured app threshold.",
    )
    parser.add_argument(
        "--output",
        default="reports/evaluation_report.json",
        help="Where to write the JSON evaluation report.",
    )
    args = parser.parse_args()

    settings = get_settings()
    threshold = args.threshold if args.threshold is not None else settings.default_similarity_threshold
    manifest = load_manifest(Path(args.manifest))
    rows, summary = evaluate_pairs(manifest, threshold)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "summary": summary,
        "pairs": [asdict(row) for row in rows],
    }
    output_path.write_text(json.dumps(payload, indent=2))
    print(json.dumps(summary, indent=2))
    print(f"Wrote evaluation report to {output_path}")


if __name__ == "__main__":
    main()
