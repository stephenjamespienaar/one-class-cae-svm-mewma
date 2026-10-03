"""Regenerate every thesis figure, generated table and derived-number file.

Canonical sources are only read; outputs go to final_report/figures/,
final_report/tables/ and planning/derived_*.json. Run from thesis/scripts/ in the
repository's pinned environment (requirements.txt), without writing bytecode, after
generating the simulation banks (see simulation/README.md):

  PYTHONDONTWRITEBYTECODE=1 python make_all_figures.py

The first run caches the frozen-model monitoring vectors in scripts/cache/ (about 20 s).
"""

import make_diagnostic_figures
import make_results_figures

if __name__ == "__main__":
    make_results_figures.main()
    make_diagnostic_figures.main()
