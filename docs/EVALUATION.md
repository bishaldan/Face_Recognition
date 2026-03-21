# Evaluation and Benchmarking

This repository now includes Docker-friendly evaluation scripts so you can measure model behavior instead of guessing.

## 1. Pair Evaluation

Create a manifest JSON like this:

```json
[
  {
    "left_image": "/app/sample-data/person_a_1.jpg",
    "right_image": "/app/sample-data/person_a_2.jpg",
    "same_person": true
  },
  {
    "left_image": "/app/sample-data/person_a_1.jpg",
    "right_image": "/app/sample-data/person_b_1.jpg",
    "same_person": false
  }
]
```

Run it:

```bash
docker compose exec app python -m app.scripts.prepare_evaluation_manifest \
  --input-root /app/sample-data \
  --output /app/reports/evaluation_manifest.json

docker compose exec app python -m app.scripts.evaluate_backend \
  --manifest /app/reports/evaluation_manifest.json \
  --output /app/reports/evaluation_report.json
```

## 2. Latency Benchmark

Run a small timing benchmark:

```bash
docker compose exec app python -m app.scripts.benchmark_verification \
  --images /app/sample-data/person_a_1.jpg /app/sample-data/person_b_1.jpg \
  --runs 5 \
  --output /app/reports/benchmark_report.json
```

## 3. What to Track Publicly

For a stronger public repository, publish:

- backend name
- model name
- threshold used
- pair accuracy on your labeled validation set
- false positive and false negative counts
- warmup and average latency

## 4. What Not to Overclaim

Do not call the system production-grade only because the app runs.

You should have:

- a real model
- a documented license
- a labeled validation set
- threshold tuning results
- at least a basic benchmark table
