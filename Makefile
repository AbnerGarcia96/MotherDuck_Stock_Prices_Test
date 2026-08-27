.PHONY: help install setup-env run-marketstack-bronze run-marketstack-silver run-marketstack-gold run-marketstack-all run-all clean

.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies with uv (creates/updates .venv)
	uv sync

setup-env: ## Copy .env.example to .env if .env doesn't exist yet
	@test -f .env || cp .env.example .env

run-marketstack-bronze: ## Ingest marketstack AAPL EOD data into the Bronze layer
	uv run python -m pipeline.run_marketstack_bronze

run-marketstack-silver: ## Dedupe/type Bronze AAPL data into the Silver layer
	uv run python -m pipeline.run_marketstack_silver

run-marketstack-gold: ## Recompute the AAPL daily-returns Gold mart from Silver
	uv run python -m pipeline.run_marketstack_gold

run-marketstack-all: ## Run the AAPL Bronze -> Silver -> Gold pipeline end to end
	$(MAKE) run-marketstack-bronze
	$(MAKE) run-marketstack-silver
	$(MAKE) run-marketstack-gold

run-all: ## Run the AAPL Bronze -> Silver -> Gold pipeline end to end (via pipeline.run_all)
	uv run python -m pipeline.run_all

clean: ## Remove the virtual environment
	rm -rf .venv
