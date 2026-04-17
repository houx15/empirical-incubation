#!/bin/bash
#SBATCH --job-name=incubation_analyze
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=32G
#SBATCH --time=08:00:00
#SBATCH --mail-type=end
#SBATCH --mail-user=yh6580@princeton.edu

# =============================================================================
# Offline analysis: parse raw quote files under $DATA_ROOT/raw/, detect
# sleeping-beauty memes, render PDFs + markdown report to a timestamped
# run directory.  No network access is used.
#
# Prerequisites (run once on a login node with internet):
#
#   cd "$SLURM_SUBMIT_DIR"
#   export UV_PROJECT_ENVIRONMENT=/scratch/network/yh6580/empirical-incubation/venv
#   uv sync
#
# Submit with:
#   sbatch --export=ALL,START=2008-08-01,END=2009-05-01 slurm/analyze.slurm
# =============================================================================

set -euo pipefail

: "${DATA_ROOT:=/scratch/network/yh6580/empirical-incubation}"
: "${UV_PROJECT_ENVIRONMENT:=${DATA_ROOT}/venv}"
: "${START:?set START=YYYY-MM-DD}"
: "${END:?set END=YYYY-MM-DD (exclusive)}"
: "${BIN_WIDTH_DAYS:=1}"

export DATA_ROOT UV_PROJECT_ENVIRONMENT

RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-${SLURM_JOB_ID:-local}"
OUT_DIR="${DATA_ROOT}/runs/${RUN_ID}"

cd "$SLURM_SUBMIT_DIR"
mkdir -p "${OUT_DIR}"

echo "=== Analysis job starting ==="
echo "  raw-dir  : ${DATA_ROOT}/raw"
echo "  out-dir  : ${OUT_DIR}"
echo "  window   : ${START} .. ${END}"
echo "  bin-days : ${BIN_WIDTH_DAYS}"

uv run empirical-incubation analyze \
    --raw-dir "${DATA_ROOT}/raw" \
    --out-dir "${OUT_DIR}" \
    --start "${START}" \
    --end "${END}" \
    --bin-width-days "${BIN_WIDTH_DAYS}"

echo "=== Analysis complete ==="
echo "Report: ${OUT_DIR}/report.md"
