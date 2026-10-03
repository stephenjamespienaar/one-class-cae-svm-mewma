# Thesis

`main.pdf` is the final STK 795 research report, "One-class hybrid SVM-CAE based MEWMA monitoring
scheme", dated 2 October 2026 (28 pages). The public manuscript corresponds to the submitted
thesis, with the handwritten signature/initials and student number omitted from the public copy.

| Path | What it is |
|---|---|
| `main.pdf` | Final report (public copy) |
| `final_report/` | LaTeX source: `main.tex`, `sections/`, `appendix/`, `figures/`, `tables/`, `thesis-lib.bib`, `UPlogohighres.jpg`, `latexmkrc` |
| `scripts/` | Regenerate the figures, the generated tables and the derived numbers from `../simulation` and `../tep-application` |
| `planning/` | `final_figure_provenance.md` (source and derivation of every figure and table) and `derived_*.json` (every derived number quoted in the text) |

## Rebuild the PDF

Requires pdfLaTeX, BibTeX and latexmk. The original was built with TeX Live 2026 (pdfTeX 1.40.29).

```bash
cd thesis/final_report
latexmk                # aux files go to build/; the PDF is copied to final_report/main.pdf (ignored by Git)
```

In this repository the title-page date is fixed to 2 October 2026 instead of the compile date.
The rebuilt PDF therefore has the same content as `main.pdf`: text, fonts, images and every
rendered page. Only the PDF's internal build timestamp and document ID differ.

## Regenerate figures and tables

The scripts only read the frozen simulation and TEP artifacts. Nothing is refitted.

```bash
# once: generate the simulation banks (see simulation/README.md)
(cd simulation && python -c "import pipeline; pipeline.generate_datasets('data/generated')")
cd thesis/scripts
PYTHONDONTWRITEBYTECODE=1 python make_all_figures.py    # Figures 1–3, 5–8, Tables 1, 5–7, derived_*.json
PYTHONDONTWRITEBYTECODE=1 python make_tep_figure4.py    # Figure 4 (TEP)
git status --short ..                                   # no output: outputs are byte-identical
```
