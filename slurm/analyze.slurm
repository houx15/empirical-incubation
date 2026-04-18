#!/bin/bash
#SBATCH --job-name=incubation_analyze
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=64G
#SBATCH --time=08:00:00
#SBATCH --mail-type=end
#SBATCH --mail-user=yh6580@princeton.edu

# =============================================================================
# Offline analysis: parse raw quote files under $DATA_ROOT/raw/, detect
# sleeping-beauty memes, render PDFs + markdown report to a timestamped
# run directory.  No network access is needed on the compute node.
#
# All analysis parameters are set below — edit this file directly and then
# submit with:  sbatch slurm/analyze.slurm
# =============================================================================

set -eo pipefail

# --- Analysis parameters (edit these) ----------------------------------------
DATA_ROOT="/scratch/network/yh6580/empirical-incubation"
START="2008-08-01"            # inclusive, YYYY-MM-DD
END="2009-05-01"              # exclusive, YYYY-MM-DD
BIN_WIDTH_DAYS=1
# -----------------------------------------------------------------------------

module purge
module load anaconda3/2023.3
conda activate llm

set -u

cd "$SLURM_SUBMIT_DIR"
export PYTHONPATH="${SLURM_SUBMIT_DIR}/src:${PYTHONPATH:-}"

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-${SLURM_JOB_ID:-local}"
OUT_DIR="${DATA_ROOT}/runs/${RUN_ID}"
mkdir -p "${OUT_DIR}"

echo "=== Analysis job starting ==="
echo "  raw-dir  : ${DATA_ROOT}/raw"
echo "  out-dir  : ${OUT_DIR}"
echo "  window   : ${START} .. ${END}"
echo "  bin-days : ${BIN_WIDTH_DAYS}"

python -m empirical_incubation.cli analyze \
    --raw-dir "${DATA_ROOT}/raw" \
    --out-dir "${OUT_DIR}" \
    --start "${START}" \
    --end "${END}" \
    --bin-width-days "${BIN_WIDTH_DAYS}"

echo "=== Analysis complete ==="
echo "Report: ${OUT_DIR}/report.md"
