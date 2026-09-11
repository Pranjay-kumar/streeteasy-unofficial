# Contributing

Install the development environment and run the complete local gate:

```bash
python -m pip install -e ".[dev,browser]"
ruff format --check .
ruff check .
pytest -q
python -m build
twine check dist/*
```

Keep normal tests offline and use sanitized fixtures. Live tests must be explicitly invoked, open visible Chrome, request no more than five search results, enrich at most one listing, and never automate a human-verification challenge.
