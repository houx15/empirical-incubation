#!/bin/bash
#SBATCH --job-name=incubation_download
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --time=04:00:00
#SBATCH --mail-type=end
#SBATCH --mail-user=yh6580@princeton.edu

# =============================================================================
# Fetch SNAP MemeTracker quote files listed in manifests/memetracker.txt into
# $DATA_ROOT/raw/.  Run on a partition that has outbound internet access;
# analysis runs on offline compute nodes.
#
# First-time setup (login node with internet):
#
#   module load anaconda3/2023.3
#   conda activate llm
#   pip install -r requirements.txt     # ensures numpy/pandas/matplotlib present
#
# Submit with:  sbatch slurm/download.slurm
# =============================================================================

set -eo pipefail

# --- Download parameters (edit these) ----------------------------------------
DATA_ROOT="/scratch/network/yh6580/empirical-incubation"
MANIFEST="${SLURM_SUBMIT_DIR}/manifests/memetracker.txt"
# -----------------------------------------------------------------------------

module purge
module load anaconda3/2023.3
conda activate llm

set -u

cd "$SLURM_SUBMIT_DIR"
export PYTHONPATH="${SLURM_SUBMIT_DIR}/src:${PYTHONPATH:-}"

mkdir -p "${DATA_ROOT}/raw"

echo "=== Download job starting ==="
echo "  manifest : ${MANIFEST}"
echo "  dest-dir : ${DATA_ROOT}/raw"

python -m empirical_incubation.cli download \
    --manifest "${MANIFEST}" \
    --dest-dir "${DATA_ROOT}/raw"

echo "=== Download complete ==="
ls -lh "${DATA_ROOT}/raw" | head
