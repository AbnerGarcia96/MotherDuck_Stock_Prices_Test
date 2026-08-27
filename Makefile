.PHONY: help install clean

.DEFAULT_GOAL := help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies with uv (creates/updates .venv)
	uv sync

clean: ## Remove the virtual environment
	rm -rf .venv
