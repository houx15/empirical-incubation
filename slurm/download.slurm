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
# $DATA_ROOT/raw/.  Run this on a partition that has outbound internet access;
# the analysis job runs on offline compute nodes.
#
# Staging (run once, from a login node with internet + uv installed):
#
#   cd "$SLURM_SUBMIT_DIR"
#   export UV_PROJECT_ENVIRONMENT=/scratch/network/yh6580/empirical-incubation/venv
#   uv sync
#
# Then submit with:   sbatch slurm/download.slurm
# =============================================================================

set -euo pipefail

: "${DATA_ROOT:=/scratch/network/yh6580/empirical-incubation}"
: "${UV_PROJECT_ENVIRONMENT:=${DATA_ROOT}/venv}"
: "${MANIFEST:=${SLURM_SUBMIT_DIR}/manifests/memetracker.txt}"

export DATA_ROOT UV_PROJECT_ENVIRONMENT

cd "$SLURM_SUBMIT_DIR"

mkdir -p "${DATA_ROOT}/raw"

echo "=== Download job starting ==="
echo "  manifest : ${MANIFEST}"
echo "  dest-dir : ${DATA_ROOT}/raw"
echo "  venv     : ${UV_PROJECT_ENVIRONMENT}"

uv run empirical-incubation download \
    --manifest "${MANIFEST}" \
    --dest-dir "${DATA_ROOT}/raw"

echo "=== Download complete ==="
ls -lh "${DATA_ROOT}/raw" | head
