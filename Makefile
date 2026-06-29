.PHONY: install plugin test test-live test-all lint clean

install:
	uv sync --extra dev

plugin:
	uv run python tools/build_plugin.py

test:
	uv run python -m pytest

test-live:
	uv run python -m pytest -m live --reruns 2 --reruns-delay 3

test-all: test test-live

lint:
	uv run ruff check .

clean:
	rm -rf engine/*.py .pytest_cache **/__pycache__ .coverage
