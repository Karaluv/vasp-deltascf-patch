#!/bin/bash
set -Eeuo pipefail
: "${REPO:?Absolute repository path}"
: "${GS:?Matching ground directory}"
: "${TDDFT:?Matching completed response directory}"
: "${SOURCE_SHA256:?Contemporaneous GS WAVECAR hash recorded for this response}"
# ROOT is one-based. Negative roots are retained by the analysis tool.
root=${ROOT_INDEX:-1}
python3 "$REPO/tools/analyze_tddft_nto.py" "$TDDFT/BSEFATBAND" \
 --wavecar "$GS/WAVECAR" --roots "$root" --json nto.json --npz nto.npz
python3 "$REPO/tools/prepare_nto_seed.py" --ground "$GS/WAVECAR" \
 --bsefatband "$TDDFT/BSEFATBAND" --root "$root" --gamma-real \
 --expected-source-sha256 "$SOURCE_SHA256" --output-dir seed \
 --saddle-template "$REPO/examples/workflows/03_auto/NTO_SADDLE"
# seed/WAVECAR is canonical. seed/WAVECAR.qqq is the unchanged NTO reference.
# A coefficient transformation is not a PAW preflight: continue with workflow02.
