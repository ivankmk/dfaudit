<img src="docs/assets/logo.png" alt="dfaudit" width="200"/>

# dfaudit

`dfaudit` is an open source Python package for modern, polished dataframe auditing visuals.

It is designed for:
- quick missing-data diagnostics,
- distribution and correlation checks,
- clean matplotlib-based output suitable for notebooks and reports.

## Usage

```python
import dfaudit as dfa

dfa.overview(df, style="vivid")
dfa.missing_matrix(df, style="vivid")
```

## Development

Install in editable mode with development tools:

```bash
uv pip install -e ".[dev]"
```
