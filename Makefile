PYTHON?=python3
VENV?=.venv
PIP=$(VENV)/bin/pip
PYTHON_BIN=$(VENV)/bin/python

.PHONY: help install lint format test run-local e2e deployed-evals adk-ui

help: ## Show available targets and their descriptions.
	@grep -E '^[a-zA-Z0-9_-]+:.*?##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "%-20s %s\n", $$1, $$2}'

$(VENV)/bin/activate: ## Create a local virtual environment and install dependencies.
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

install: $(VENV)/bin/activate ## Install project dependencies into the virtual environment.

lint: install ## Run Ruff, mypy, and other lint checks.
	$(VENV)/bin/ruff check agent tests
	$(VENV)/bin/mypy agent tests

format: install ## Apply Black formatting to the codebase.
	$(VENV)/bin/black agent tests

test: install ## Execute the full pytest suite (unit + integration + eval markers).
	$(VENV)/bin/pytest

e2e: install ## Run local end-to-end orchestrator evaluations against the mocked Todo API.
	$(VENV)/bin/pytest -m e2e

deployed-evals: install ## Run deployed agent evaluations; requires DEPLOYED_AGENT_URL to be set.
	$(VENV)/bin/pytest -m deployed

run-local: install ## Start the TodoOrchestrator CLI for interactive local testing.
	bash scripts/launch_local.sh

adk-ui: install ## Launch the ADK developer UI via gcloud (requires VERTEX_PROJECT_ID and VERTEX_LOCATION).
	@if [ -z "$$VERTEX_PROJECT_ID" ] || [ -z "$$VERTEX_LOCATION" ]; then \
	echo "VERTEX_PROJECT_ID and VERTEX_LOCATION must be set in the environment or .env"; \
	exit 1; \
	fi
	@gcloud alpha aiplatform agents developer-tools browse --project "$$VERTEX_PROJECT_ID" --location "$$VERTEX_LOCATION"
