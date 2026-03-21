.PHONY: up down rebuild logs ps test lint typecheck seed shell evaluate benchmark manifest onnx-up

up:
	docker compose up --build -d

down:
	docker compose down

rebuild:
	docker compose build --no-cache

logs:
	docker compose logs -f app

ps:
	docker compose ps

test:
	docker compose exec app pytest

lint:
	docker compose exec app ruff check .

typecheck:
	docker compose exec app mypy app tests

seed:
	docker compose exec app python -m app.scripts.seed_demo

shell:
	docker compose exec app sh

evaluate:
	@test -n "$(MANIFEST)" || (echo "Usage: make evaluate MANIFEST=/app/path/to/manifest.json" && exit 1)
	docker compose exec app python -m app.scripts.evaluate_backend --manifest "$(MANIFEST)"

benchmark:
	@test -n "$(IMAGES)" || (echo "Usage: make benchmark IMAGES='/app/image1.jpg /app/image2.jpg'" && exit 1)
	docker compose exec app python -m app.scripts.benchmark_verification --images $(IMAGES)

manifest:
	@test -n "$(INPUT_ROOT)" || (echo "Usage: make manifest INPUT_ROOT=/app/sample-data" && exit 1)
	docker compose exec app python -m app.scripts.prepare_evaluation_manifest --input-root "$(INPUT_ROOT)"

onnx-up:
	docker compose -f docker-compose.yml -f docker-compose.onnx.yml up --build -d
