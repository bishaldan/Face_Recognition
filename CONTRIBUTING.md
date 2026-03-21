# Contributing

Thanks for considering a contribution.

## Development Workflow

This repository is Docker-first. You do not need a local Python virtual environment.

### Start the stack

```bash
cp .env.example .env
docker compose up --build -d
```

### Run checks

```bash
docker compose exec app pytest
docker compose exec app ruff check .
docker compose exec app mypy app tests
```

### Useful commands

```bash
make up
make test
make lint
make typecheck
make logs
```

## Pull Request Guidelines

- Keep changes focused and easy to review.
- Add or update tests when behavior changes.
- Update documentation when commands, environment variables, or workflows change.
- Do not add pretrained model weights to the repository.
- If a change affects privacy or security, call that out clearly in the PR description.

## Areas Where Contributions Help Most

- Better ONNX model adapters
- Liveness / presentation attack detection
- Accessibility improvements
- Threshold calibration tooling
- Benchmarks and reproducible evaluation scripts
- Better demo assets and screenshots

