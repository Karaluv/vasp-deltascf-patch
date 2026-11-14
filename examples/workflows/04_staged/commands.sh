#!/bin/bash
set -Eeuo pipefail
: "${REPO:?}" "${GS:?}" "${SEED:?}" "${PREFLIGHT:?}" "${VASP_SADDLE_GAM:?}"
python3 - "$PREFLIGHT/paw.json" <<'PY'
import json,sys
assert json.load(open(sys.argv[1]))['full_paw_seed_identity_passed']
PY
: "${GEOMETRY:?Geometry matching the response WAVECAR, normally TDDFT/POSCAR or final GS/CONTCAR}"
previous=$PREFLIGHT
for mode in PROJECT REFLECT SECANT; do
 directory="stage_$mode"
 mkdir "$directory"
 cp "$GS/POTCAR" "$GS/KPOINTS" "$directory/"
 cp "$GEOMETRY" "$directory/POSCAR"
 cp "$GEOMETRY" "$directory/POSCAR.qqq"
 cp "$previous/WAVECAR" "$directory/WAVECAR"
 cp "$SEED/WAVECAR.qqq" "$directory/WAVECAR.qqq"
 cp "$REPO/examples/workflows/04_staged/NTO_SADDLE.$mode" "$directory/NTO_SADDLE"
 python3 "$REPO/tools/merge_incar.py" "$GS/INCAR" \
  --overlay "$REPO/examples/workflows/04_staged/INCAR.$mode.fragment" --output "$directory/INCAR"
 (cd "$directory" && VASP_GAM="$VASP_SADDLE_GAM" bash "$REPO/tools/run_single_rank.sh")
 python3 "$REPO/tools/analyze_paw_nto.py" --wswq "$directory/WSWQ" --eigenval "$directory/EIGENVAL" \
  --ref-hole-band 191 --ref-part-band 192 --require-target --json "$directory/paw.json"
 flags=()
 [[ $mode != SECANT ]] || flags+=(--require-residual)
 python3 "$REPO/tools/summarize_saddle.py" "$directory" --json "$directory/summary.json" --csv "$directory/iterations.csv" "${flags[@]}"
 previous=$PWD/$directory
done
# Restarts retain orbitals, not Damped velocity/secant history. AUTO avoids these restarts.
