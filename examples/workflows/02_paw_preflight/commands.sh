#!/bin/bash
set -Eeuo pipefail
: "${REPO:?}" "${GS:?}" "${SEED:?}" "${VASP_STOCK_GAM:?Compatible original executable}"
: "${GEOMETRY:?Geometry matching the response WAVECAR, normally TDDFT/POSCAR or final GS/CONTCAR}"
mkdir preflight
cp "$GS/POTCAR" "$GS/KPOINTS" preflight/
cp "$GEOMETRY" preflight/POSCAR
cp "$GEOMETRY" preflight/POSCAR.qqq
cp "$SEED/WAVECAR" "$SEED/WAVECAR.qqq" preflight/
python3 "$REPO/tools/merge_incar.py" "$GS/INCAR" \
 --overlay "$REPO/examples/workflows/02_paw_preflight/INCAR.fragment" --output preflight/INCAR
(cd preflight && VASP_GAM="$VASP_STOCK_GAM" bash "$REPO/tools/run_single_rank.sh")
python3 "$REPO/tools/analyze_paw_nto.py" --wswq preflight/WSWQ \
 --eigenval preflight/EIGENVAL --n-occ 191 --ref-hole-band 191 --ref-part-band 192 \
 --hole-band 192 --expect-seed --json preflight/paw.json --csv preflight/bands.csv
