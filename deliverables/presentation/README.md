# Presentation materials

- [Editable PowerPoint](offshore_nearshore_information.pptx): 13 slides in 16:9 format, including a reference slide; narration is also embedded in speaker notes.
- [PDF preview](presentation_preview.pdf): independently rendered visual preview of the same content, not a PowerPoint export. Font wrapping may differ slightly in PowerPoint.
- [Speaker script](speaker_script.md) and [Word script](speaker_script.docx): approximately 1136 spoken words for slides 1–12 (around 9–11 minutes, depending on pace).

Uses the existing final report, original primary estimates and three existing scientific figures. No JIDT calculations, new statistical analyses or significance claims. Positive lag is offshore(t) → nearshore(t+τ). Main slides omit k sensitivity.

Rebuild from the repository root:

```sh
.venv/bin/python -m pip install -r config/requirements-presentation.txt
.venv/bin/python src/build_presentation.py
```

Check the editable deck in PowerPoint or Keynote before recording, especially figure labels and line wrapping. Confirm the actual assessment time limit; 10 minutes is a working assumption, not a verified course requirement.
