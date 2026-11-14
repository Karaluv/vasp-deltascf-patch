#!/bin/bash
set -Eeuo pipefail
: "${REPO:?}" "${GS:?}" "${SEED:?}" "${PREFLIGHT:?}" "${VASP_SADDLE_GAM:?Compatible patched executable}"
python3 - "$PREFLIGHT/paw.json" <<'PY'
import json,sys
assert json.load(open(sys.argv[1]))['full_paw_seed_identity_passed']
PY
: "${GEOMETRY:?Geometry matching the response WAVECAR, normally TDDFT/POSCAR or final GS/CONTCAR}"
mkdir auto
cp "$GS/POTCAR" "$GS/KPOINTS" auto/
cp "$GEOMETRY" auto/POSCAR
cp "$GEOMETRY" auto/POSCAR.qqq
cp "$PREFLIGHT/WAVECAR" auto/WAVECAR
cp "$SEED/WAVECAR.qqq" auto/WAVECAR.qqq
cp "$SEED/NTO_SADDLE" auto/NTO_SADDLE
python3 "$REPO/tools/merge_incar.py" "$GS/INCAR" \
 --overlay "$REPO/examples/workflows/03_auto/INCAR.fragment" --output auto/INCAR
(cd auto && VASP_GAM="$VASP_SADDLE_GAM" bash "$REPO/tools/run_single_rank.sh")
python3 "$REPO/tools/summarize_saddle.py" auto --json auto/summary.json --csv auto/iterations.csv --require-residual
python3 "$REPO/tools/analyze_paw_nto.py" --wswq auto/WSWQ --eigenval auto/EIGENVAL \
 --ref-hole-band 191 --ref-part-band 192 --require-target --json auto/paw.json --csv auto/bands.csv
