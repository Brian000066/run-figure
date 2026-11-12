#!/bin/bash
# Double-click in Finder (or run ./run_structure_figures.command) to run the
# Fig. 3 panels with shared-structure (chain) DAGs.
cd "$(dirname "$0")"
python3 run_structure_figures.py "$@"
echo
echo "Finished. Press Enter to close."
read
