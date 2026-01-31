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
	ruff check cmd/ pkg/ tests/
	ruff format --check cmd/ pkg/ tests/

# Build single-file binary with PyInstaller (current OS only)
# Example for each OS (run on that OS):
#   pyinstaller -F -n kubectl-manifest-clean -m cmd.manifest_clean.main
bin:
	pyinstaller -F -n kubectl-manifest-clean -m cmd.manifest_clean.main

build: bin

clean:
	rm -rf build/ dist/ *.egg-info .eggs/
	rm -rf cmd/__pycache__ pkg/__pycache__ .pytest_cache .ruff_cache
	rm -rf cmd/manifest_clean/__pycache__ pkg/manifest_clean/__pycache__
	rm -f kubectl-manifest-clean.spec
