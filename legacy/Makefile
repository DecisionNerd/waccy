.PHONY: help lint typecheck test test-cov bdd docs-build docs-serve pre-push

help:
	@echo "Available targets:"
	@echo "  make lint       - Run ruff"
	@echo "  make typecheck  - Run mypy"
	@echo "  make test       - Run pytest"
	@echo "  make test-cov   - Run pytest with the CI coverage gate"
	@echo "  make bdd        - Run outcome-oriented BDD specs"
	@echo "  make docs-build - Build docs with MkDocs"
	@echo "  make docs-serve - Serve docs locally with MkDocs"
	@echo "  make pre-push   - Run local checks before pushing a PR branch"

lint:
	uv run ruff check

typecheck:
	uv run mypy src/waccy

test:
	uv run pytest

test-cov:
	uv run pytest --cov=src/waccy --cov-report=term-missing --cov-report=xml --cov-fail-under=90

bdd:
	uv run pytest tests/bdd -q -m "bdd or outcome"

docs-build:
	uv run --group docs mkdocs build --strict

docs-serve:
	uv run --group docs mkdocs serve

pre-push: lint typecheck bdd test-cov docs-build
