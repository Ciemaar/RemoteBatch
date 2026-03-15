# Tooling Evaluation

This document outlines the evaluation and adoption of various development tools for this project, aligning with modern Python 3.12+ standards.

## 1. Formatter: `ruff format` vs. `black`

- **Evaluation**: `black` has long been the standard uncompromising Python formatter. However, `ruff format` has recently emerged as a Rust-based alternative that is >99% compatible with Black's style but executes exponentially faster. Since we are already using `ruff` for linting, adopting `ruff format` unifies our toolchain.
- **Decision**: Adopt `ruff format`. It reduces the number of dependencies, simplifies configuration in `pyproject.toml`, and significantly improves CI and local formatting speed.

## 2. Linter: `ruff` vs. `flake8` / `pylint`

- **Evaluation**: Legacy codebases often rely on `flake8` and `pylint`, coupled with numerous plugins (like `pydocstyle` for docstrings). `ruff` consolidates all these tools into a single, incredibly fast binary. It supports `flake8` rules, `pylint` rules, and `pydocstyle` (via the `D` rule selection).
- **Decision**: Adopt `ruff`. We have configured it in `pyproject.toml` to catch a wide array of issues (e.g., standard errors, pyupgrade suggestions, list comprehensions, and missing Google-style docstrings).

## 3. Type Checker: `pyright` vs. `mypy` vs. `pyre` vs. `ty`

- **Evaluation**:
  - `mypy` is the official Python type checker. It is strict but can be slow and sometimes difficult to configure for highly dynamic code without stubs. In this project, `mypy` flagged 5 errors.
  - `pyright` is Microsoft's fast type checker (used in VSCode/Pylance). It is generally faster and handles un-annotated or complex libraries (like PyQt6 without extensive stubs) slightly differently. In this project, `pyright` flagged 18 errors, primarily complaining about `PyQt6` methods possibly returning `None` (e.g., `menuBar().addMenu(...)`).
  - `pyre-check` (by Meta) is highly performant and strict, but requires a more involved setup (`pyre init`, `.pyre_configuration`, Watchman integration if using Buck). Testing it showed that it is not as "plug-and-play" as pyright/mypy for simple projects without Watchman.
  - `ty` (Astral's Ty / experimental type checker, or similar fast CLI tools) is incredibly fast but still in earlier stages of adoption compared to the maturity of pyright or mypy. It flagged 19 diagnostics on par with pyright regarding PyQt6 optional returns and unresolved attributes.
- **Decision**: Adopt `pyright`. It provides a tighter integration with modern IDEs (like VSCode), is fast for CI, and has a mature, easy-to-use configuration. To manage the strictness around PyQt6's optional returns, we use `typeCheckingMode = "basic"` in `pyproject.toml`, which provides a good balance between catching real bugs and avoiding false positives from untyped third-party libraries. `pyre` was rejected due to setup friction, and `ty` while promising, does not currently offer a distinct advantage over pyright's ecosystem integration.

## 4. Testing Framework: `pytest` vs. `unittest`

- **Evaluation**: `unittest` is built-in but requires boilerplate class structures. `pytest` is the industry standard due to its concise fixture system, powerful assertions, and massive plugin ecosystem (`pytest-cov`, `pytest-qt`, `pytest-mock`).
- **Decision**: Adopt `pytest`. We have also adopted `pytest-cov` to enforce a baseline code coverage, ensuring new PRs do not degrade testing standards. `hypothesis` is also used for property-based testing of core models.

## 5. Documentation Formatter: `mdformat`

- **Evaluation**: Markdown files often drift in style. `mdformat` is an uncompromising Markdown formatter that ensures all documentation (like `README.md` and `AGENTS.md`) follows a strict CommonMark/GFM style.
- **Decision**: Adopt `mdformat` as a mandatory CI check.

## 6. Polling & Retry Utilities: `tenacity` vs. `schedule` vs. `while True`

- **Evaluation**: The backend server (`server.py`) historically relied on a raw `while True` loop with explicit `sleep()` calls for polling S3 and handling temporary connection errors.
  - **`while True`**: Simple but brittle. Prone to silent failures, complicated nested `try/except` blocks, and difficult to test cleanly.
  - **`schedule`**: Great for running cron-like tasks (e.g., "every day at 10 AM"), but overkill for a continuous polling daemon.
  - **`tenacity`**: An excellent, mature library specifically designed to simplify retry logic, implement exponential backoff, and manage wait states gracefully without cluttering business logic.
- **Decision**: Adopt `tenacity`. We can replace the fragile `try/except Exception: sleep(180)` logic around the S3 polling loop with a robust `@retry` decorator, providing exponential backoff and cleaner code structure for the server daemon.

## Summary of Adopted Toolchain

- **Linting & Formatting**: `ruff`
- **Type Checking**: `pyright`
- **Testing**: `pytest` (with `pytest-cov`, `pytest-mock`, and `hypothesis`)
- **Markdown Formatting**: `mdformat`
- **Retry Logic**: `tenacity`
