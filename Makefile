.PHONY: install-dev precommit-install precommit-run format lint test

# Install development dependencies
install-dev:
	pip install ruff black pre-commit pytest
	pip install -e app/api[dev]
	pip install -e app/trader[dev]

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
	cd app/api && PYTHONPATH=../.. mypy -p mirai_api
	cd app/trader && mypy .

# Run tests
test:
	pytest app/api/tests
	pytest app/trader/tests