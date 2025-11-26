.PHONY: help setup run down docker clean

VENV := .venv
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn
APP := app.main:app

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

setup: ## Create venv and install dependencies
	python3 -m venv $(VENV)
	$(PIP) install -r requirements.txt

run: ## Run the server with hot reload
	$(UVICORN) $(APP) --reload

down: ## Stop any running server
	@pkill -f "uvicorn $(APP)" 2>/dev/null || true

docker: ## Build and run with Docker
	docker build -t evaluations-api .
	docker run --rm \
		--add-host=host.docker.internal:host-gateway \
		-p 8000:8000 \
		-e SNAPAUTH_BASE_URL=http://host.docker.internal:8080 \
		evaluations-api

clean: ## Remove venv and database
	rm -rf $(VENV) app.db __pycache__ app/__pycache__
