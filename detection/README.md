## Development Workflow

- Create or refresh the virtual environment with `uv venv`.
- Install project dependencies from `pyproject.toml` via `uv sync`.
- Run the test suite with `uv run pytest -q` before pushing changes.

## Pre-Commit Hook

This repository uses `pre-commit` (invoked through `uv`) to ensure all tests pass before commits land.

1. Install the hook tooling with `uv tool run pre-commit install`.
2. Commits will now execute `uv run pytest -q`; resolve any failures before retrying the commit.

To trigger the hook manually, run `uv tool run pre-commit run --all-files`.
