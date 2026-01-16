.PHONY: update_packages test typecheck clean format all mypy scc coverage install venv

VENV_DIR = venv
PYTHON = python3
PIP = $(VENV_DIR)/bin/pip
PYTEST = $(VENV_DIR)/bin/pytest
MYPY = $(VENV_DIR)/bin/mypy
ISORT = $(VENV_DIR)/bin/isort
BLACK = $(VENV_DIR)/bin/black

venv:
	$(PYTHON) -m venv $(VENV_DIR)
	$(PIP) install --upgrade pip

install: venv
	$(PIP) install -r requirements.txt

update_packages: venv
	@echo "Checking for outdated packages..."
	@outdated=$$($(PIP) list --outdated --format=columns | awk '{print $$1}' | grep -v "Package"); \
	if [ -z "$$outdated" ]; then \
		echo "No outdated packages found."; \
	else \
		echo "Outdated packages:"; \
		$(PIP) list --outdated --format=columns; \
		echo "\nUpdating outdated packages..."; \
		echo "$$outdated" | xargs -n1 $(PIP) install -U; \
		echo "\nPackages updated successfully!"; \
	fi

test:
	$(PYTEST) tests/

coverage:
	$(PYTEST) --cov=src --cov-report=html

typecheck:
	$(MYPY) --ignore-missing-imports --explicit-package-bases --check-untyped-defs src/

clean:
	rm -rf **pycache**
	rm -rf src/__pycache__
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf $(VENV_DIR)

format:
	$(ISORT) src/
	$(ISORT) tests/
	$(BLACK) src/
	$(BLACK) tests/

all: clean format typecheck test

mypy: typecheck

scc:
	scc --exclude-ext=txt .