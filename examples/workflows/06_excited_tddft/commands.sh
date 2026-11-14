#!/bin/bash
set -Eeuo pipefail
: "${REPO:?}" "${S4:?Matched accepted excited directory}" "${VASP_STOCK_RESPONSE_GAM:?Compatible original response build}"
mkdir excited_tdhf
cp "$S4/POSCAR" "$S4/POTCAR" "$S4/KPOINTS" "$S4/WAVECAR" excited_tdhf/
# No ground CHGCAR or old WAVEDER: density is reconstructed from the excited input.
python3 "$REPO/tools/merge_incar.py" "$S4/INCAR" \
 --overlay "$REPO/examples/workflows/06_excited_tddft/INCAR.fragment" --output excited_tdhf/INCAR
(cd excited_tdhf && VASP_GAM="$VASP_STOCK_RESPONSE_GAM" bash "$REPO/tools/run_single_rank.sh")
python3 "$REPO/tools/analyze_tddft_nto.py" excited_tdhf/BSEFATBAND \
 --roots 1,2,3 --wavecar "$S4/WAVECAR" --json excited_response_nto.json --npz excited_response_nto.npz
# Negative roots remain in the output. This does not establish an emission spectrum.
# Do not replace the original optimization reference with the first excited-response NTO.
