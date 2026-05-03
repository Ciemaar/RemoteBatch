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

# Composite Agentic Instructions: Modernization Guide

These instructions represent the accumulated best practices for modernizing
legacy Python codebases based on constraints extracted from multiple
organizational repositories.

## 1. Architecture & Configuration

- **Project Layout**: You must mandate a strict `src`-based directory layout.
- **Data Privacy & LLMs:** You must treat data as private and local-first. You
  must never send sensitive data to third-party cloud LLM APIs. You must always
  default to local inference servers (e.g., Ollama).
- **Package Management**: You must mandate `uv` exclusively for environment management. You must prohibit
  `pip`, `poetry`, and `pipenv`. You must ensure `uv.lock` is always checked
  into version control to guarantee deterministic environments, and you must
  configure CI to verify that it is up-to-date.
- **Single Source of Truth**: You must place all configurations in
  `pyproject.toml`. `tox.ini` may be an exception to this.
- **Configuration Model**: You must mandate `pydantic-settings` universally as
  the only acceptable way to load and validate environment variables and
  configurations.
- **CLI Framework**: You must mandate `click` for CLIs and you must prohibit
  `argparse`. You must also require a `--verbose` flag that sets logging to
  `DEBUG`. However, do not use `click` to handle arguments for PyQt5/6 desktop applications, let PyQt handle parsing natively.

## 2. Python Syntax & Types

- **Version Upgrade:** You must upgrade codebases to modern Python (3.12, 3.13,
  3.14+). You must always use the new idioms and APIs provided by the Python
  versions supported by the project. When an older version of Python is no
  longer supported, you must upgrade the code to use the new features that are
  now available.
- **Dependency Upgrades:** You must upgrade dependencies in the code to their
  newest supported version and implement their newer features and idioms. You
  must update from unsupported legacy modules to more modern, supported
  alternatives. You must only replace dependencies when they are no longer
  supported by the community and after evaluating replacement tools.
- **Type Annotations:**
  - You must remove legacy type imports (`typing.List`, `typing.Optional`,
    `typing.Dict`, `typing.Union`).
  - You must use modern built-in generics (`list[str]`, `dict[str, int]`) and
    the union operator (`str | None`).
  - You must avoid `typing.Any` wherever possible. You should prefer targeted
    type hints or omission in heavily dynamic closures (like those using
    `mypy`).
- **Ternary Operators:** Never use the `x or y` shortcut syntax for non-boolean
  results (e.g., `value or 0.0`). Python evaluates values like `0.0` or `""` as
  falsy, leading to unintended behavior. Instead, always use explicit ternary
  operations like `x if x is not None else y`.
- **Imports:** You must strictly enforce top-of-file imports. You must avoid
  inline/local imports in all normal cases, only using them to break circular
  imports or support plugins and similar rare cases.
- **Logging vs Print:** You must always use the `logging` module (or
  `structlog`). You must never use `print()` for log information.

## 3. File & IO Operations

- **Pathlib Native:** You must strip out `os.path` and traditional string-based
  file paths. You must always use `pathlib.Path` for file access, path
  construction, and read/write operations.
- **Resource Cleanup:** You must require context managers (e.g.,
  `tempfile.TemporaryDirectory`) over manual teardowns like `shutil.rmtree`.

## 4. Tooling & Environment

- **Linting & Formatting:**
  - You must migrate away from combinations of `flake8`, `black`, and `isort`.
  - You must adopt `ruff` as the universal, high-speed linter and formatter.
  - For Markdown documentation, you must standardize on `mdformat`.
- **Type Checking:** You must standardize on `pyright` in strict mode as the
  universal default for all projects. `mypy` is an approved fallback only for
  codebases that rely heavily on metaprogramming and dynamic duck-typing.
- **Git Hooks:** You must require `pre-commit` for local linting, formatting,
  type-checks, and running tests.

## 5. Testing

- **Tooling:** You must always use `tox`, `pytest`, and `hypothesis` as the
  universal test runner defaults, with other tools allowed as needed.
- **Unit vs Integration:** You must use `unittest.mock` as the standard for
  isolated unit tests, while you must use ephemeral databases via
  `docker compose` as the required pattern for integration tests.
- **Coverage:** You must ensure test coverage is a constant increase with each
  PR. You must configure CI to fail if the PR reduces the overall coverage
  percentage baseline.
- **Documentation Verification:** You must explicitly test the features
  documented in the user documentation to ensure they work as described. You
  must update both documentation and tests as you add new features.

## 6. Application Architecture

- **Database Migrations:** You must automate database migrations for all project
  types. Tools like `alembic` or `yoyo` are recommended, but a specific
  framework is not strictly required as long as the process is automated and
  version-controlled.
- **Web Frameworks:** It is not necessary to migrate web frameworks if they are
  still supported. If it is necessary to migrate, you must migrate to the most
  similar modern, supported framework while avoiding complex JavaScript.
  - You must use **FastAPI** (with `htmx` and Jinja2) to replace complex JS
    Single Page Applications where appropriate.
  - For applications where standard WSGI, strict simplicity, or the extensive
    extension ecosystem is better suited than FastAPI's async-first approach,
    you should prefer **Flask**.
- **Persistence:** You must ensure all web database calls are asynchronous. You
  must migrate synchronous `pymongo` to
  `motor.motor_asyncio.AsyncIOMotorClient`.

## 7. Security & Safety

- You must remove `assert` statements from production code (they can be disabled
  by Python optimization flags). Instead, you must raise an appropriate built-in
  exception (e.g., `ValueError`) or a custom exception derived from an
  appropriate built-in.
- **Serialization:** You must always prefer YAML with `yaml.safe_load` for
  serialization. You should only use `cloudpickle` or other options when there
  is a clear special benefit. You must avoid insecure serializers like `pickle`
  for untrusted data.

## 8. Documentation & Comments

- **Docstring Enforcement:** You must enforce Ruff's `pydocstyle` (D) ruleset
  for docstrings.
- **Meaningful Context:** You must prohibit auto-generated/placeholder
  docstrings.
- **Documentation Files:** You must require specific root files:
  - `README.md`: High-level project overview, quickstart, and core purpose.
  - `SOURCES.md`: You must maintain a bibliography of sources considered in a
    `SOURCES.md` (or similar) file. For each source, you must provide a link and
    commentary explaining its relevance or how it was used.
  - `USER_GUIDE.md`: Detailed instructions on how end-users should interact with
    the application or library.
  - `DEVELOPER_GUIDE.md`: Architecture details, local setup, and contributing
    guidelines. **You must document new systems or tools under the assumption
    that the developer does not know them.**
  - If documentation for any of these files needs more than one file, you must
    create additional files under `docs/`.
- **Agent Context Files:** You must require AI agent context files (`AGENTS.md`
  and/or `.github/copilot-instructions.md`). These must contain
  machine-actionable constraints, explicit anti-patterns, and context
  specifically formatted for LLM consumption rather than human-readable
  tutorials. You must explicitly capture all instructions within these
  modernization guidelines as agent instructions within these files.
- **Agentic Session Documentation:** You must document agentic prompts, plans,
  and reports. For each agentic session, you must create a markdown file under
  `prompts/` that specifies the composite prompt that would be used to
  approximately repeat the session on a similar project. You must update this
  prompt as details are added or changed. You must capture pre-implementation
  planning in a markdown file under `plans/`, and post-implementation reports in
  a markdown file under `reports/`. All of these files must be formatted as
  standard markdown.

## 9. CI/CD & Tool Evaluation

- **CI Pipelines:** You must require GitHub Actions for automated checks.

- **Proposing New Tools:** You must require documenting new tool evaluations in
  `docs/tooling_evaluation.md` before adoption. The evaluation must document the
  tool's purpose, alternatives considered, and setup instructions, assuming the
  reader has no prior context. When proposing a new development dependency, you
  must evaluate it based on community support and adoption, `pyproject.toml`
  compatibility, execution speed, and false-positive rates.
