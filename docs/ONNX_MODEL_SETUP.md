# ONNX Model Setup Guide

This project ships with a demo recognition backend by default. To turn it into a more serious verification system, plug in a licensed or self-trained ONNX embedding model.

## What You Need

- An ONNX face embedding model
- Clear documentation for the model license
- A small validation set for threshold tuning

## Environment Variables

Update `.env`:

```env
RECOGNITION_BACKEND=onnx
ONNX_MODEL_PATH=/models/your-face-embedder.onnx
ONNX_INPUT_SIZE=112
```

## Mount the Model into Docker

One clean option is to mount a local `models/` directory:

```yaml
services:
  app:
    volumes:
      - ./models:/models:ro
```

Then rebuild:

```bash
docker compose up --build -d
```

## Recommended Workflow

1. Start with one ONNX model you are legally allowed to use.
2. Confirm `/api/system/info` shows the correct backend and model name.
3. Run the evaluation and benchmark scripts.
4. Tune the threshold using your labeled validation pairs.
5. Document the tradeoffs in the README before claiming production readiness.

## Important Warning

Do not commit third-party model binaries into this repository unless you are sure the license allows redistribution.
