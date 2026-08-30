# AI Agent Instructions

This project is a RemoteBatch job processing application using Python 3.12+, featuring a PyQt6 GUI client and a server daemon. You must adhere to the following strict modern standards when assisting with code.

## Architecture & Configuration

- **Project Layout**: Use a standard `src`-based directory layout (`src/remotebatch/`).
- **Single Source of Truth**: All dependencies, build configurations, and tool settings MUST be centralized in `pyproject.toml`.
- **Environment Management**: Strictly require `uv`. The use of `pip`, `poetry`, and `pipenv` is prohibited, and `uv.lock` must be checked into version control.
- **Key Development Commands**:
  - `uv lock` (generate lockfile)
  - `uv pip install -e .[dev]` (install dependencies)
  - `uv run pre-commit run --all-files` (lint/format)
  - `uv run pyright` (type check)
  - `uv run pytest` or `uv run tox` (test)
- **Environment Config**: Always use `pydantic-settings` for strict runtime environment variable validation.
- **Web Frameworks**: Mandate FastAPI (with htmx and Jinja2) over JS SPAs, or Flask for strict WSGI simplicity. Database operations must be asynchronous (e.g., `motor_asyncio`).
- **CLI & GUI Frameworks**: CLI applications must typically be built using `click` with a mandatory `--verbose` flag for `DEBUG` logging. For PyQt desktop GUI components, native `QCommandLineParser` must be used instead of `argparse` or `click` to properly handle arguments without intercepting `QApplication` and causing segmentation faults.
- **Desktop Notifications**: For cross-platform desktop notifications, use actively maintained libraries like `plyer` over obsolete frameworks like `osso`.

## Syntax & Strictness

- **Python Version**: Write code optimized for Python 3.12+. Use modern built-in features.
- **Modern Typing**: Use built-in generics and the pipe operator for unions (e.g., `list[str]`, `dict[str, int]`, `str | None`). Do not import `List`, `Dict`, `Optional`, or `Union` from the legacy `typing` module.
- **Type Checking**: Type checking strictly uses `pyright` in 'strict' mode. Do not bypass the type checker with `typing.Any`. For highly dynamic parameters, use standard abstract base classes.
- **Control Flow**: Implicit ternary operator shortcuts (e.g., `x or y`) are prohibited for non-boolean results. Explicit ternary statements (e.g., `x if x is not None else y`) must be used instead.
- **File Operations**: Exclusively use `pathlib.Path` objects; traditional `os.path` and string-based file paths are prohibited.
- **Serialization**: Prefer YAML with `yaml.safe_load`, avoiding insecure serializers like `pickle` for untrusted data.
- **Cleanup & Resources**: Use context managers (e.g., `tempfile.TemporaryDirectory`) for automatic cleanup instead of manual teardowns like `shutil.rmtree`.
- **Error Handling**: Production code must not contain `assert` statements; explicit built-in or custom exceptions must be raised instead.
- **Logging**: Exclusively use the `logging` or `structlog` modules. `print()` statements are prohibited.

## Static Analysis & Formatting

- **Linting & Formatting**: Mandated universally via `ruff` and `mdformat`, enforced through `pre-commit` hooks. Top-of-file imports are strictly enforced.
- **Ruff Rule PLR2004**: Enforced; magic values used in comparisons (including within tests) must be extracted into descriptively named variables.
- **Git Hooks**: `pre-commit` MUST be set up to run all linting, formatting, and type-checks locally before allowing a commit or push.

## Testing

- **Framework**: Use `tox`, `pytest`, and `hypothesis`, with isolated unit tests using `unittest.mock`. Overall coverage percentages must never decrease, and features in `USER_GUIDE.md` must be explicitly tested.
- **Tox Coverage**: When using `tox` with `isolated_build = True`, test coverage must explicitly target the installed package directory (e.g., `{envsitepackagesdir}/[package]`) rather than the local `src/` directory.
- **PyQt Testing**: Headless testing of PyQt components requires exporting `QT_QPA_PLATFORM=offscreen` or wrapping the test execution command with `xvfb-run`.
- **QCommandLineParser Testing**: When testing `QCommandLineParser` with `pytest` and `mocker`, mock `QtWidgets.QApplication` and `QCommandLineParser.process` to prevent segmentation faults and test runner aborts caused by native C++ `exit()` calls.

## Documentation & Comments

- **Docstring Enforcement**: Strictly enforce Ruff's `pydocstyle` (`D`) rules for all modules, classes, and methods. Docstrings MUST convey business logic, edge cases, and architectural context.
- **Documentation Files**: Required project files include `README.md`, `SOURCES.md`, `USER_GUIDE.md`, `DEVELOPER_GUIDE.md`, and `docs/tooling_evaluation.md`.
- **Agentic Sessions**: Must be thoroughly documented using markdown files capturing prompts (`prompts/`), pre-implementation plans (`plans/`), and post-implementation reports (`reports/`). Machine-actionable constraints must be preserved in `AGENTS.md`.

## Workflow & Privacy

- **Git/PR Workflow**: When working on an existing or previous branch (e.g., rebasing or merging), intermediate features added to the main branch must not be removed. All merged branches and their matching PRs must be explicitly referenced in commit messages and any new PR descriptions.
- **Data Privacy**: Prioritized: default to local inference servers (e.g., Ollama) and never send sensitive data to third-party cloud LLM APIs.
- **CI/CD**: GitHub Actions MUST be set up to run type-checking, ruff linting/formatting, mdformat, and pytest test suites automatically on all pushes and PRs.
