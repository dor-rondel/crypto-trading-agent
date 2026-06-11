.PHONY: install format lint test spell check clean

PYTHON ?= uv run python
SRC_DIR := src
TEST_DIR := tests

install:
	uv sync

format:
	uv run ruff format .

lint:
	uv run ruff check .
	uv run pylint $(SRC_DIR)
	uv run mypy $(SRC_DIR)

test:
	uv run pytest $(TEST_DIR)

spell:
	uv run codespell .

check:
	uv run ruff format --check .
	uv run ruff check .
	uv run pylint $(SRC_DIR)
	uv run mypy $(SRC_DIR)
	uv run pytest $(TEST_DIR)
	uv run codespell .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[cod]" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf .venv
