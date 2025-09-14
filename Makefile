.PHONY: install-dev precommit-install precommit-run format lint test clean build docker-build

# Install development dependencies
install-dev:
	pip install -r requirements.txt
	pip install ruff black pre-commit pytest mypy

# Install pre-commit hooks
precommit-install:
	pre-commit install

# Run pre-commit on all files
precommit-run:
	pre-commit run --all-files

# Format code using ruff and black
format:
	ruff format .
	black .

# Lint code using ruff and mypy
lint:
	ruff check .
	mypy .

# Run tests
test:
	pytest

# Clean cache and build files
clean:
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -type f -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache .mypy_cache
	rm -rf dist build *.egg-info

# Build Docker images
docker-build:
	docker-compose -f infra/docker-compose.yml build

# Build and start services
docker-up:
	docker-compose -f infra/docker-compose.yml up -d

# Stop services
docker-down:
	docker-compose -f infra/docker-compose.yml down