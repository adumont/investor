.DEFAULT_GOAL := run

run:
	uv run streamlit run src/app.py

ruff:
	uv run ruff check --fix .
	uv run ruff format .

sync:
	uv sync --extra dev
