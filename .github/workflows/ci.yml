name: CI

on:
  workflow_dispatch:
    inputs:
      package_path:
        description: 'Path to package directory'
        required: true
        default: 'part5_decorators'
      run_ty:
        description: 'Run ty type checker'
        required: false
        default: false
        type: boolean
      run_pyrefly:
        description: 'Run pyrefly type checker'
        required: false
        default: false
        type: boolean
  push:
    branches: [main, master]
  pull_request:
    branches: [main, master]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version-file: .python-version

      - name: Install dependencies
        run: uv sync --group lint --group test

      - name: Run ruff check
        run: uv run ruff check "part5_decorators"

      - name: Run ruff format
        run: uv run ruff format --check "part5_decorators"

      - name: Run wemake-python-styleguide
        run: uv run flake8 "part5_decorators"

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version-file: .python-version

      - name: Install dependencies
        run: uv sync --group lint --group test

      - name: Run mypy
        run: uv run mypy "part5_decorators"

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v5

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version-file: .python-version

      - name: Install dependencies
        run: uv sync --group lint --group test

      - name: Run pytest
        run: |
          if [ -d "part5_decorators/tests" ]; then
            uv run pytest "part5_decorators/tests" -v
          else
            echo "No tests directory found in part5_decorators"
          fi