# AI Agent Instructions

This project uses strict modern Python 3.12+ standards. You must adhere to the following when assisting with code.

## Architecture & Configuration

- **Project Layout**: Use a standard `src`-based directory layout (`src/remotebatch/`).
- **Single Source of Truth**: All dependencies, build configurations, and tool settings MUST be centralized in `pyproject.toml`. Do not create or update `setup.py`, `setup.cfg`, `tox.ini`, or `requirements.txt`.
- **Environment Config**: Always use `pydantic-settings` for strict runtime environment variable validation. Do not use raw `os.environ` or `os.getenv` directly in application logic.
- **CLI Framework**: Always use `click` for building Command Line Interfaces. Do not use `argparse` or `optparse`.

## Syntax & Type Strictness

- **Python Version**: Write code optimized for Python 3.12+. Use modern built-in features.
- **Modern Typing**: Use built-in generics and the pipe operator for unions (e.g., `list[str]`, `dict[str, int]`, `str | None`). Do not import `List`, `Dict`, `Optional`, or `Union` from the legacy `typing` module.
- **The Any Anti-Pattern**: Do not bypass the type checker with `typing.Any`. For highly dynamic parameters, use standard abstract base classes (`collections.abc.Mapping`, `collections.abc.Callable`) or omit the type hint entirely rather than polluting the codebase with `Any`.
- **Cleanup & Resources**: Use context managers (e.g., `tempfile.TemporaryDirectory`) for automatic cleanup. Avoid manual teardown commands like `shutil.rmtree`.
- **File Operations**: Always use `pathlib.Path` objects. Never use raw strings for file paths.

## Static Analysis & Formatting

- **Linting & Formatting**: Use Ruff exclusively for all Python code. Do not introduce `pylint`, `flake8`, `isort`, or `black`.
- **Type Checking**: Use Pyright.
- **Markdown**: Format all markdown files using `mdformat` to enforce strict 80-character text wrapping.
- **Git Hooks**: `pre-commit` MUST be set up to run all linting, formatting, and type-checks locally before allowing a commit or push.

## Testing

- **Framework**: Write all tests using `pytest`. Use `hypothesis` for property-based testing where applicable.
- **Isolation**: Use `unittest.mock` to mock network requests and API endpoints without hitting live external services.
- **Coverage**: Maintain test coverage and ensure pytest-cov configurations are strictly within `pyproject.toml`.

## Documentation & Comments

- **Docstring Enforcement**: You must write docstrings for all modules, classes, and methods satisfying Ruff's `pydocstyle` (`D`) ruleset.
- **Meaningful Context**: Docstrings MUST convey business logic, edge cases, and architectural context. Do not write auto-generated placeholder text.
- **Documentation Files**: Maintain `README.md`, `USER_GUIDE.md`, and `DEVELOPER_GUIDE.md` at the root of the repository.

## CI/CD & Tool Evaluation

- **CI Pipelines**: GitHub Actions MUST be set up to run type-checking, ruff linting/formatting, mdformat, and pytest test suites automatically on all pushes and PRs.
- **Proposing New Tools**: If proposing a new development dependency, you must evaluate based on `pyproject.toml` compatibility, execution speed, and false-positive rates, and document findings in `TOOL_EVALUATION.md` before implementation.

## Git & Branch Management

- **Branch Merging & Rebasing**: When working on an existing or previous branch (e.g., rebasing or merging), features must not be removed if they've been added to the main branch in the intermediate interval.
- **Commit Comments & PRs**: All the branches being merged in, as well as their matching PRs, must be referenced in the commit comments and any new PRs.
