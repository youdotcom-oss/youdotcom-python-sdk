# Contributing to This Repository

Thank you for your interest in contributing to the You.com Python SDK! This SDK is hand-maintained (not generated) and we welcome pull requests.

## How to Report Issues

If you encounter any bugs or have suggestions for improvements, please open an issue on GitHub. When reporting an issue, please provide as much detail as possible to help us reproduce the problem. This includes:

- A clear and descriptive title
- Steps to reproduce the issue
- Expected and actual behavior
- Any relevant logs, screenshots, or error messages
- Information about your environment (e.g., operating system, software versions)
    - For example can be collected using the `npx envinfo` command from your terminal if you have Node.js installed

## Pull Requests

1. Fork the repository and create a branch from `main`.
2. Make your changes. Follow existing code style and patterns.
3. Add or update tests as needed. Run `pytest tests/ --ignore=tests/test_live.py --ignore=tests/test_performance.py` for unit tests (live tests require `YDC_API_KEY`).
4. Run `mypy src/youdotcom/` to ensure type safety.
5. Update documentation (README, CHANGELOG, `docs/` directory) if your change adds or modifies public API surface.
6. Open a pull request with a clear description of the change.

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
pip install mypy pylint pyright pytest pytest-asyncio
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv sync --dev
```

## Contact

If you have any questions or need further assistance, please feel free to reach out by opening an issue.

Thank you for your understanding and cooperation!

The Maintainers
