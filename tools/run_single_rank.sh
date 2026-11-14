#!/bin/bash
# Portable example launcher; the executable/architecture is selected explicitly.
set -uo pipefail
: "${VASP_GAM:?Set VASP_GAM to the compatible licensed vasp_gam executable}"
[[ -x "$VASP_GAM" ]] || { echo 'VASP_GAM is not executable' >&2; exit 2; }
[[ ${SLURM_NTASKS:-1} == 1 ]] || { echo 'This patch supports one MPI rank' >&2; exit 2; }
for input in INCAR POSCAR POTCAR KPOINTS WAVECAR; do
 [[ -f "$input" ]] || { echo "Missing $input" >&2; exit 2; }
done
for output in OUTCAR vasprun.xml vasp.stdout vasp.exit input.sha256; do
 [[ ! -e "$output" ]] || { echo "Use a fresh directory: $output exists" >&2; exit 2; }
done
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
if [[ -f NTO_SADDLE ]]; then
 python3 "$script_dir/check_nto_controls.py" NTO_SADDLE || exit $?
 [[ -f WAVECAR.qqq && -f POSCAR.qqq ]] || { echo 'Missing paired NTO reference files' >&2; exit 2; }
fi
export OMP_NUM_THREADS=1 OMP_DYNAMIC=false MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
ulimit -s unlimited
inputs=(INCAR POSCAR POTCAR KPOINTS WAVECAR)
for file in NTO_SADDLE WAVECAR.qqq POSCAR.qqq; do [[ ! -f "$file" ]] || inputs+=("$file"); done
sha256sum -- "$VASP_GAM" "${inputs[@]}" > input.sha256 || exit $?
case ${VASP_LAUNCHER:-mpirun} in
 mpirun) mpirun -np 1 "$VASP_GAM" > vasp.stdout 2>&1 ;;
 srun) srun --ntasks=1 "$VASP_GAM" > vasp.stdout 2>&1 ;;
 direct) "$VASP_GAM" > vasp.stdout 2>&1 ;;
 *) echo 'VASP_LAUNCHER must be mpirun, srun or direct' >&2; exit 2 ;;
esac
result=$?
printf '%s\n' "$result" > vasp.exit
exit "$result"
