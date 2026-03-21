# Sample Data Layout

Do not commit real personal face data to this repository.

For local evaluation, organize data like this:

```text
sample-data/
  person_a/
    image_01.jpg
    image_02.jpg
  person_b/
    image_01.jpg
    image_02.jpg
```

Then generate a manifest for evaluation:

```bash
docker compose exec app python -m app.scripts.prepare_evaluation_manifest \
  --input-root /app/sample-data \
  --output /app/reports/evaluation_manifest.json
```

