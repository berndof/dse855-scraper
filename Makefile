ENV_FILE := ${PWD}/.env

install:
	@echo "Installing dependencies..."
	@uv sync
	@echo "Installing playwright and chromium headless..."
	@uv run --env-file ${ENV_FILE} playwright install --with-deps --only-shell chromium

task:
	@echo "Running task..."
	@uv run --env-file ${ENV_FILE} helpers/cron_task.py --create

clean_task:
	@echo "Cleaning task..."
	@uv run --env-file ${ENV_FILE} helpers/cron_task.py --delete

clean_state:
	@echo "Cleaning state file..."
	@-rm browsers/state.json > /dev/null 2>&1

uninstall:
	@echo "Uninstalling dependencies..."
	@make clean_state > /dev/null 2>&1
	@-uv run --env-file ${ENV_FILE} playwright uninstall > /dev/null 2>&1
	@-rm -rf .venv > /dev/null 2>&1

.PHONY: install, task, clean_task, clean_state, uninstall