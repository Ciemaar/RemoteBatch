# AI Agent Instructions

This project uses modern Python 3.12+ standards.

## Tooling

- **Linting/Formatting**: Ruff is used. Run `ruff check` and `ruff format`.
- **Type Checking**: Pyright is used. Run `pyright`.
- **Testing**: Pytest is used. Run `pytest`.

## Code Standards

- Use type hints for all function arguments and return values.
- Use `list[str]`, `str | None` syntax (Python 3.10+ style).
- Avoid deprecated functions like `os.tmpnam`. Use `tempfile` module.
- Use `tarfile.extractall(filter='data')`.
- Docstrings should follow Google style.

## Architecture

- AWS S3/Boto3 logic should be abstracted.
- `LocalQueue` is the default implementation for local testing.
- GUI uses PyQt6.
