# Final deliverables

The [project README](../README.md) provides an overview of the analysis, documentation and supporting results.

- [Scientific report — Word](final_scientific_report.docx): editable final manuscript.
- [Scientific report — Markdown](final_scientific_report.md): inspect the text, numerical tables and figures directly.
- [Assessment coverage](../README.md#limitations): analysis scope and unresolved statistical inference.
- [Figures](figures/): three selected figures, each as PNG and PDF: direct information contrasts, temporal sensitivity and descriptive height scatterplots.
- [Primary values](primary_information_summary.csv), [site differences](between_site_contrasts.csv), and [temporal sensitivity](temporal_sensitivity_reused.csv): saved supporting results, not new calculations.

The figures and numerical values are preserved copies of the existing results. JSON manifests/checks document the original report build. This is the final descriptive two-deployment comparison; no validated wave-data significance is claimed.

Rebuild documents using `.venv/bin/python src/consolidate_final_report.py` from the project root. Optional Word dependencies are in config/requirements-report.txt. The narrative template is docs/templates/final_report.md. Existing exports can mention old paths because their contents were preserved during organization; historical references are resolved using config/legacy_paths.json.

The three selected figures can be regenerated from existing results using `.venv/bin/python src/make_presentation_figures.py`. This does not run JIDT.
