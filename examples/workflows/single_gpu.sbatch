#!/bin/bash
#SBATCH --job-name=nto-dscf-example
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=2
#SBATCH --gpus=1
#SBATCH --mem=32G
#SBATCH --time=04:00:00
set -Eeuo pipefail
# Add your site's partition/account, load the compiler/CUDA/MPI environment matching
# the executable, and start in a fresh, fully prepared calculation directory.
: "${REPO:?Absolute public repository path}"
: "${VASP_GAM:?Explicit compatible licensed vasp_gam executable}"
export VASP_LAUNCHER=srun
bash "$REPO/tools/run_single_rank.sh"
