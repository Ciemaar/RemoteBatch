1. **Agent Session Documentation & File Structure Updates**:
   - Merge provided modernization guidelines into `AGENTS.md`.
   - Create `SOURCES.md` as required.
   - Move `TOOL_EVALUATION.md` to `docs/tooling_evaluation.md`.
   - Create `prompts/`, `plans/`, and `reports/` directories and save the initial prompt and plan.
1. **Environment & Dependencies**:
   - Run `uv lock` to generate `uv.lock`.
   - Configure `tox.ini` for automated testing using `uv`.
   - Update `pyproject.toml` to set Pyright `typeCheckingMode = "strict"`.
1. **CI/CD Configuration**:
   - Create `.github/workflows/ci.yml` that checks out code, installs `uv`, runs `pre-commit`, and runs `tox`.
1. **Code Refactoring (Pathlib, Logging, Syntax)**:
   - Replace all `print()` statements with `logging.getLogger(__name__).info(...)` or `.debug(...)` in `src/`.
   - Refactor `os.path` to `pathlib.Path` in `src/remotebatch/view/__init__.py`.
   - Add a `--verbose` flag to CLI entry points (`BatchManager.py`, `RemoteBatch.py`, `server.py`) that sets logging level to `DEBUG`.
   - Fix Ruff linting errors (e.g. `tests/test_queues.py` `PLC0415`, `SIM108` in `src/remotebatch/tabdialog.py`).
1. **Strict Type Checking Fixes**:
   - Fix Pyright errors by adding type hints, removing `typing.Any` logic, and using modern generics to satisfy `strict` mode.
1. **Documentation Verification & Testing**:
   - Write tests for features documented in `USER_GUIDE.md` using `click.testing.CliRunner`.
   - Ensure coverage percentage increases or is maintained.
1. **Pre-commit**:
   - Complete pre-commit steps to ensure proper testing, verifications, reviews, and reflections are done.
1. **Submit**:
   - Push branch and create pull request.
