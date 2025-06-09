ENV_FILE := ${PWD}/.env

install:
	@echo "Installing dependencies..."
	@uv sync
	@echo "Installing playwright and chromium headless..."
	@uv run --env-file ${ENV_FILE} playwright install --with-deps --only-shell chromium

.PHONY: install