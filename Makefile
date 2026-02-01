# kubectl-manifest-clean Makefile
# Python 3.11+ required

.PHONY: help install test lint bin build clean

help:
	@echo "Targets: install, test, lint, build, clean, bin"

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v

lint:
	ruff check entrypoint/ pkg/ tests/
	ruff format --check entrypoint/ pkg/ tests/

# Build single-file binary with PyInstaller (current OS only)
# Example for each OS (run on that OS):
#   pyinstaller -F -n kubectl-manifest-clean -m entrypoint.manifest_clean.main
bin:
	pyinstaller -F -n kubectl-manifest-clean -m entrypoint.manifest_clean.main

build: bin

clean:
	rm -rf build/ dist/ *.egg-info .eggs/
	rm -rf entrypoint/__pycache__ pkg/__pycache__ .pytest_cache .ruff_cache
	rm -rf entrypoint/manifest_clean/__pycache__ pkg/manifest_clean/__pycache__
	rm -f kubectl-manifest-clean.spec
