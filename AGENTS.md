# Repository Guidelines

## Project Structure & Module Organization
`app/` contains the Flask application. Blueprints are split by concern: `app/auth/`, `app/main/`, `app/api/`, and `app/errors/`. Shared setup lives in `app/__init__.py`, data models in `app/models.py`, and CLI registration in `app/cli.py`. Templates and static assets live under `app/templates/` and `app/static/`. Database migrations are in `migrations/`. Tests mirror the app layout under `tests/`, for example `tests/app/auth/test_routes.py`.

## Build, Test, and Development Commands
Use Poetry for day-to-day development.

- `poetry install`: install runtime and dev dependencies.
- `poetry run pytest`: run the full test suite. This is also what CI executes.
- `poetry run pytest --cov=app`: run tests with coverage output.
- `poetry run flask run`: start the local development server.
- `make run`: run the Flask server through the repository helper target.
- `make icu`: build `libsqliteicu.so`, required when SQLite ICU collation support is needed locally.

## Coding Style & Naming Conventions
Python code uses 4-space indentation and standard PEP 8 naming: `snake_case` for functions and modules, `PascalCase` for classes, and `UPPER_CASE` for constants. Keep route handlers grouped by feature in the existing blueprint modules such as `routes_products.py` or `routes_settings.py`. Format with `poetry run black .`, sort imports with `poetry run isort .`, and use `poetry run pylint app tests` for lint checks before opening a PR.

## Testing Guidelines
Pytest is the test framework. Add tests under `tests/` in the nearest matching package and name files `test_*.py`. Prefer focused route and utility coverage following existing examples in `tests/app/main/` and `tests/app/auth/`. No explicit coverage gate is defined, but new behavior should ship with regression tests.

## Commit & Pull Request Guidelines
Recent commits use short, imperative summaries such as `refactor authentication routes and add session management for last seen tracking`. Follow that style: one-line, lowercase subject, describing the shipped change. PRs should include a concise description, linked issue when applicable, notes on config or migration impact, and screenshots for template or UI changes.

## Configuration & Security Notes
Configuration is loaded from `.env` via `config.py`. Do not commit real secrets, production mail settings, or database credentials. The default local database is `app.db`; treat it as local state, not source-controlled configuration.
