# Release Notes Draft: v0.1.0

## Highlights

- Rebuilt the original Tkinter prototype into a Docker-first FastAPI web application
- Added operator login, enrollment, verification, audit logs, settings, and health endpoints
- Added Postgres-backed metadata storage and S3-compatible image storage with MinIO
- Added a pluggable recognition backend with demo and ONNX-ready paths
- Added evaluation and benchmark scripts for future model validation
- Added public-release repository assets: MIT license, security policy, contribution guide, and CI

## Why This Release Matters

This is the first version that treats the project like a serious engineering artifact instead of only a proof of concept.

It is now:

- easier to run
- easier to understand
- easier to extend
- more honest about privacy and model licensing

## Known Limitations

- The default backend is still a demo embedder, not a production-grade model
- No real ONNX benchmark table is published yet
- Screenshots and demo GIF still need to be added
- Liveness / PAD is not implemented yet

## Suggested GitHub Release Title

`v0.1.0 - FaceProof, a Docker-first face verification platform`
