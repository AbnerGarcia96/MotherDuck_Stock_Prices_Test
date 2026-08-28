.PHONY: help install clean deploy-dives deploy-flights download-dives download-flights

.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies with uv (creates/updates .venv)
	uv sync

clean: ## Remove the virtual environment
	rm -rf .venv

deploy-dives: ## Push Dives/*.tsx to MotherDuck (needs MOTHERDUCK_TOKEN, see .env.example)
	uv run python scripts/deploy/deploy_dives.py

deploy-flights: ## Push Flights/*/main.py to MotherDuck (needs MOTHERDUCK_TOKEN, see .env.example)
	uv run python scripts/deploy/deploy_flights.py

download-dives: ## Pull remote Dives back into Dives/, for review
	uv run python scripts/deploy/download_dives.py

download-flights: ## Pull remote Flights back into Flights/, for review
	uv run python scripts/deploy/download_flights.py
