.PHONY: lint format-isort format-black type-check all

lint:
	@echo "Running Ruff for linting..."
	@poetry run ruff check ./release_manager --fix

format-isort:
	@echo "Sorting imports with iSort..."
	@poetry run isort ./release_manager

format-black:
	@echo "Formatting code with Black..."
	@poetry run black ./release_manager

type-check:
	@echo "Running static type checks with mypy..."
	@poetry run mypy ./release_manager

cc: lint format-isort format-black type-check

run:
# export PATH="/home/user/.local/bin:$PATH"
	poetry run python -m release_manager
