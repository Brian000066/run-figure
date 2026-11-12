"""Run the Fig. 3 panels with shared-structure DAGs.

Same simulator, methods, cost formulas and figure definitions as
run_ten_figures.py; the only difference is how shared subtasks are generated:
each shared group is a chain of 2-4 connected subtasks reused in 2-4 task
graphs (instead of single random nodes).  Results go to
results/structure_figures/<timestamp>/ so the original runs are untouched.

Default panels (same as Fig. 3):
  (a) Fig 1  tasks / total cost
  (b) Fig 10 shared subtasks / total cost   (x = number of shared subtask kinds)
  (c) Fig 13 delay constraint / bandwidth cost      (from the Fig 4 sweep)
  (d) Fig 15 required features / communication cost (from the Fig 9 sweep)
  (e) Fig 12 IoTs / RSMA groups                     (from the Fig 2 sweep)
  (f) Fig 2  IoTs / total cost

Usage (all options of run_ten_figures.py work, e.g. --runs, --new, --resume):
  python3 run_structure_figures.py --new
  python3 run_structure_figures.py --figures 1,10 --runs 100 --new
  RSMA_SHARED_CHAIN_RANGE=2,3 python3 run_structure_figures.py --new
"""
from __future__ import annotations

import os
import sys

# Must be set before run_ten_figures is imported; worker processes inherit them.
os.environ.setdefault("RSMA_SHARED_CHAIN_RANGE", "2,4")
os.environ.setdefault("RSMA_RESULTS_SUBDIR", "structure_figures")

DEFAULT_FIGURES = "1,10,13,15,12,2"


def _with_default_figures(argv: list[str]) -> list[str]:
    if any(arg == "--figures" or arg.startswith("--figures=") for arg in argv):
        return argv
    return argv + ["--figures", DEFAULT_FIGURES]


if __name__ == "__main__":
    import run_ten_figures

    sys.argv = [sys.argv[0]] + _with_default_figures(sys.argv[1:])
    print(f"Shared-structure mode: chains of "
          f"{os.environ['RSMA_SHARED_CHAIN_RANGE'].replace(',', '-')} subtasks; "
          f"results in results/{os.environ['RSMA_RESULTS_SUBDIR']}/")
    run_ten_figures.main()
