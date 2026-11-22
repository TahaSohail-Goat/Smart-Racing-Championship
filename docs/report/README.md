# Technical report

The report follows assignment section 9.2: title page, introduction, architecture,
models/rules, algorithm design and correctness, integration, testing, experiments,
advanced challenges/limitations/future work, conclusion and references.

## Build and review

From the project root:

```powershell
.\.venv\Scripts\python.exe scripts/build_report.py
.\.venv\Scripts\python.exe scripts/render_report_preview.py
```

The PDF is written to `output/pdf/technical-report.pdf`. Rendered pages are in
`output/report-review/`. The build uses `technical-report.md`,
`report-details.json`, the official university mark under `assets/`, and the
stored experimental analysis/raw measurements. Formatting does not rerun the
benchmark or replace the recorded measurement environment. ReportLab, Pillow
and PyMuPDF are required for building and reviewing this report in the existing
development environment.

## Presentation decision

The requested academic layout uses A4 pages, 22 mm left/right body margins,
29 mm top/bottom body margins, an inset 12 mm page border, numbered headings,
a linked contents list, running headers and numbered footers. Text, tables and
the institutional mark print in black ink on white. Game photography is omitted.
The original downloaded university marks are preserved with provenance.

Title-page identities are user-supplied, not inferred. The recorded source test
run is distinct from the earlier stored benchmark run. A complete human season,
final archive checks, demo and viva must not be claimed solely from report output.
