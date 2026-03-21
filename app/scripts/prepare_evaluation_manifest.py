import argparse
import itertools
import json
from pathlib import Path


def collect_people(input_root: Path) -> dict[str, list[Path]]:
    people: dict[str, list[Path]] = {}
    for person_dir in sorted(path for path in input_root.iterdir() if path.is_dir()):
        images = sorted(
            [
                path
                for path in person_dir.iterdir()
                if path.is_file() and path.suffix.lower() in {".jpg", ".jpeg", ".png"}
            ]
        )
        if images:
            people[person_dir.name] = images
    return people


def build_manifest(people: dict[str, list[Path]], max_positive_pairs: int, max_negative_pairs: int) -> list[dict]:
    manifest: list[dict] = []

    for _, images in people.items():
        positive_pairs = list(itertools.combinations(images, 2))[:max_positive_pairs]
        for left, right in positive_pairs:
            manifest.append(
                {
                    "left_image": str(left),
                    "right_image": str(right),
                    "same_person": True,
                }
            )

    person_names = sorted(people.keys())
    negative_count = 0
    for left_name, right_name in itertools.combinations(person_names, 2):
        for left_image in people[left_name]:
            for right_image in people[right_name]:
                manifest.append(
                    {
                        "left_image": str(left_image),
                        "right_image": str(right_image),
                        "same_person": False,
                    }
                )
                negative_count += 1
                if negative_count >= max_negative_pairs:
                    return manifest
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a labeled evaluation manifest from per-person image folders."
    )
    parser.add_argument("--input-root", required=True, help="Root directory containing one folder per person.")
    parser.add_argument(
        "--output",
        default="reports/evaluation_manifest.json",
        help="Where to write the generated manifest JSON.",
    )
    parser.add_argument("--max-positive-pairs", type=int, default=8)
    parser.add_argument("--max-negative-pairs", type=int, default=20)
    args = parser.parse_args()

    input_root = Path(args.input_root)
    people = collect_people(input_root)
    manifest = build_manifest(people, args.max_positive_pairs, args.max_negative_pairs)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, indent=2))

    print(
        json.dumps(
            {
                "people": len(people),
                "pairs_generated": len(manifest),
                "output": str(output_path),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()

