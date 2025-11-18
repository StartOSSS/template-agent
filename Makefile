PYTHON?=python3
VENV?=.venv
PIP=$(VENV)/bin/pip
PYTHON_BIN=$(VENV)/bin/python

.PHONY: install lint format test run-local

$(VENV)/bin/activate:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install: $(VENV)/bin/activate

lint: install
	$(VENV)/bin/ruff check agent tests
	$(VENV)/bin/mypy agent tests

format: install
	$(VENV)/bin/black agent tests

test: install
	$(VENV)/bin/pytest

run-local: install
	bash scripts/launch_local.sh
