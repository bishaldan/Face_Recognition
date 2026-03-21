# FaceProof Implementation Plan

## Goal

Ship a polished, Docker-first, privacy-aware face verification platform that is credible for open source use, educational value, and future client adaptation.

## Phase 1: Foundation

- Finalize Docker-first development workflow
- Lock down data model, migrations, and storage boundaries
- Keep the legacy Tkinter prototype as historical reference only
- Stabilize operator auth, audit logging, and settings management

## Phase 2: Recognition Quality

- Replace the demo embedder with a licensed or self-trained ONNX embedding model
- Add model registry metadata and environment-driven model switching
- Create repeatable threshold calibration scripts and benchmark datasets
- Add optional quality overlays for camera guidance
- Publish evaluation outputs and latency notes in the repository

## Phase 3: Product Hardening

- Add role separation for operators and admins
- Add soft-delete / re-enable flow for users
- Improve failure messaging for camera access and low-quality captures
- Add image retention policy settings and backup/restore documentation

## Phase 4: Open Source Excellence

- Add screenshots, short demo video, and benchmark tables
- Publish clear comparison notes for demo vs production model backends
- Add GitHub issue templates, contribution workflow, and project board
- Write architecture docs that explain the full data flow simply

## Phase 5: Future Impact

- Optional liveness / PAD support
- Optional attendance mode built on top of verification primitives
- Optional cloud deployment reference
- Optional packaged desktop wrapper for offline-first users

## Definition of Done for Public Release

- Docker quick start works on a clean machine
- README is complete and visually strong
- Security, license, contribution, and roadmap files are present
- CI runs lint and tests
- The project clearly documents privacy and model licensing boundaries
- At least one real ONNX model path is documented and benchmarked

## Immediate Next Execution Steps

- Add screenshots and one short demo GIF to the README
- Plug in a real ONNX model and verify `/api/system/info`
- Run `evaluate_backend.py` on labeled image pairs
- Run `benchmark_verification.py` and publish results
- Write a first `v0.1.0` release note with architecture, privacy, and benchmark caveats
