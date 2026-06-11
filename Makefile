.PHONY: install format lint test spell check clean

PYTHON ?= python3
SRC_DIR := src
TEST_DIR := tests

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

format:
	ruff format .

lint:
	ruff check .
	pylint $(SRC_DIR)

test:
	pytest $(TEST_DIR)

spell:
	codespell .

check:
	ruff format --check .
	ruff check .
	pylint $(SRC_DIR)
	pytest $(TEST_DIR)
	codespell .

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	rm -rf .pytest_cache
	rm -rf .ruff_cache