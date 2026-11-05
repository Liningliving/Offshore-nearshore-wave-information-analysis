# Optional dependency sets

Run these from the project root:

```sh
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pip install -r config/requirements-report.txt
```

The base file supplies NumPy/pandas/Matplotlib. The report extra adds python-docx and includes ../requirements.txt relative to its own location.

- **legacy_paths.json**: compact aliases needed to read older saved artifact paths. This replaces the bulky migration records.
- **verified_sources.json**: SHA-256 values of the original scientific source CSVs, used by figure/report checks.
- **cleanup_verification.json**: small record of the removal of superseded/cache files and preservation checks.
