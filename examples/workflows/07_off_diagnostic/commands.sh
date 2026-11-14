#!/bin/bash
set -Eeuo pipefail
: "${REPO:?}" "${S4:?}" "${VASP_SADDLE_GAM:?}"
mkdir off_probe
cp "$S4/POSCAR" "$S4/POTCAR" "$S4/KPOINTS" "$S4/WAVECAR" "$S4/WAVECAR.qqq" off_probe/
cp "$S4/POSCAR" off_probe/POSCAR.qqq
cp "$REPO/examples/workflows/07_off_diagnostic/NTO_SADDLE" off_probe/NTO_SADDLE
python3 "$REPO/tools/merge_incar.py" "$S4/INCAR" \
 --overlay "$REPO/examples/workflows/07_off_diagnostic/INCAR.fragment" --output off_probe/INCAR
(cd off_probe && VASP_GAM="$VASP_SADDLE_GAM" bash "$REPO/tools/run_single_rank.sh")
python3 "$REPO/tools/summarize_saddle.py" off_probe --json off_probe/summary.json --csv off_probe/iterations.csv
# First trace = pre-update input. The ordinary OFF update follows: retain original S4.
