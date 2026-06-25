# Contributing

Thanks for your interest in improving GitHub Action Runner! Contributions of all
kinds are welcome — bug reports, fixes, docs, and features.

## Development Setup

This project uses [uv](https://docs.astral.sh/uv/) for dependency management and
targets **Python >= 3.14**.

```bash
# Install dependencies (including dev tools)
uv sync

# Run the test suite
uv run pytest

# Lint
uv run ruff check .
```

> If you prefer pip: `pip install -r requirements.txt` and run `pytest` / `ruff`
> from your environment.

## Before Opening a Pull Request

- Make sure `pytest` passes. Coverage must stay **≥ 90%** (`fail_under = 90` in
  `pyproject.toml`).
- Make sure `ruff check .` is clean.
- Never commit secrets or real data — see [SECURITY.md](SECURITY.md). Verify
  `git status` shows no `.env`, `pem/*.pem`, or database files.
- Keep changes focused and describe the motivation in the PR description.

## Reporting Issues

Use the issue tracker for bugs and feature requests. For security vulnerabilities,
follow [SECURITY.md](SECURITY.md) instead of opening a public issue.
