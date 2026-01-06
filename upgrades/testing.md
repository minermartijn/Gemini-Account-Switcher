# Testing Improvements Needed

## Issue
There are currently no automated tests or test suite present in the project. This makes it difficult to ensure reliability, prevent regressions, and confidently refactor or upgrade the codebase.

## Recommendation
- Add a `tests/` directory at the project root.
- Use `pytest` as the test runner (standard for modern Python projects).
- Write unit tests for all major functions in `utils.py` and CLI commands in `main.py`.
- Consider adding integration tests for account switching scenarios.
- Optionally, set up GitHub Actions or another CI service to run tests on every push/PR.

## Example Structure
```
GeminiAccountSwitcher/
├── tests/
│   ├── test_utils.py
│   └── test_main.py
```

## Benefits
- Increases code reliability and maintainability.
- Makes it easier for contributors to add features or fix bugs.
- Prevents accidental breakage of core features.