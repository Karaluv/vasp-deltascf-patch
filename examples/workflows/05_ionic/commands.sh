#!/bin/bash
set -Eeuo pipefail
: "${REPO:?}" "${S4:?Completed accepted SECANT directory}" "${VASP_SADDLE_GAM:?Compatible patched executable}"
# Uses the original matched S4 reference, not a TDHF output or a new NTO root.
python3 "$REPO/tools/summarize_saddle.py" "$S4" --json accepted_s4.json --require-residual
mkdir ionic
cp "$S4/POSCAR" "$S4/POTCAR" "$S4/KPOINTS" "$S4/WAVECAR" "$S4/WAVECAR.qqq" ionic/
cp "$S4/POSCAR" ionic/POSCAR.qqq
cp "$S4/WAVECAR.qqq" ionic/reference.nto
cp "$REPO/examples/workflows/05_ionic/NTO_SADDLE" ionic/NTO_SADDLE
python3 "$REPO/tools/merge_incar.py" "$S4/INCAR" \
 --overlay "$REPO/examples/workflows/05_ionic/INCAR.fragment" --output ionic/INCAR
(cd ionic && VASP_GAM="$VASP_SADDLE_GAM" bash "$REPO/tools/run_single_rank.sh")
python3 "$REPO/tools/export_ionic_checkpoints.py" ionic --point last \
 --checksums --write-poscar --output-dir accepted_ionic
# The exporter can also inspect a live/truncated XML in a separate analysis directory.
# Optimizer/velocity/curvature history is not restored by this export.
