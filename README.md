# empirical-incubation

Detect **sleeping-beauty** patterns — an *early bump → dormancy → late explosion* shape — in mention-count time series such as SNAP MemeTracker quotes.

The detector is stricter than the standard Ke et al. (2015) beauty coefficient: it requires a visible early rise, a genuinely quiet middle phase, and a late peak that dominates the early one.

## Quick start

On the cluster, after the one-time setup below:

```bash
# login node (needs internet)
python -m empirical_incubation.cli download --manifest manifests/memetracker.txt \
    --dest-dir /scratch/network/yh6580/empirical-incubation/raw

# compute node (offline)
sbatch slurm/analyze.slurm
```

The analyze job writes `report.md`, top-N trajectory PDFs, and feature histograms to `$DATA_ROOT/runs/<timestamp>-<jobid>/`.

## Layout

```
src/empirical_incubation/
  parse.py            SNAP format streaming parser
  detect.py           three-phase feature extractor + qualification check
  plot.py             per-trajectory PDF renderer
  download.py         resumable HTTP download
  pipeline.py         run_analysis: runs stages 1-4 end-to-end
  stages/
    clean.py          stage 1: raw gz -> (phrase, iso_ts) tsv.gz
    aggregate.py      stage 2: tsv.gz -> phrases.txt + timelines.npy (int32 matrix)
    score.py          stage 3: timelines.npy -> features.csv
    report.py         stage 4: features.csv -> report.md + plots (top-N only)
  cli.py              subcommands: download, clean, aggregate, score, report, analyze
tests/                pytest suite — synthetic fixtures only, no real-data dependency
manifests/memetracker.txt   9 SNAP MemeTracker9 URLs (2008-08 .. 2009-04)
slurm/analyze.slurm         offline analysis job (runs all four stages)
slurm/download.slurm        reference only — compute nodes are offline, run download on a login node
```

Outputs live under `$DATA_ROOT` (default `/scratch/network/yh6580/empirical-incubation/`) and are **never** committed to this repo.

## Pipeline design

The analyze workflow is split into four disk-persisted stages. Each stage streams its input, writes a small intermediate artifact, and hands it off to the next stage — so peak memory is bounded per-stage, every stage is independently resumable / inspectable, and threshold tuning only re-runs the cheap tail stages.

```
raw/*.txt.gz                         ~GB gzipped SNAP dumps
  │
  │ clean  (stage 1, constant memory, per-file streaming)
  ▼
stages/clean/*.tsv.gz                compact (phrase, iso_ts) records
  │
  │ aggregate  (stage 2, two-pass: count -> filter -> dense int32 matrix)
  ▼
stages/aggregate/
  phrases.txt                        one phrase per line
  timelines.npy                      int32 matrix (n_phrases, n_bins)
  config.json                        start, end, bin_width_days, min_total_mentions
  │
  │ score  (stage 3, mmap-read rows, compute features row-by-row)
  ▼
stages/score/features.csv            one row per phrase, all features + qualified flag
  │
  │ report  (stage 4, sort by amplitude_ratio, render top-N only)
  ▼
report.md
plots/<phrase-id>.pdf                at most top_n qualified
hist_amplitude_ratio.pdf, hist_gap_ratio.pdf
```

Why staged: earlier versions held all phrase trajectories in memory simultaneously and OOM-killed at 32 GB on MemeTracker9. Staging trades extra disk I/O for a bounded memory footprint and plots only the top-N qualified phrases instead of every qualifier.

## Local setup

```bash
uv sync
uv run pytest
```

## Cluster setup (one-time, login node)

```bash
git clone git@github.com:houx15/empirical-incubation.git
cd empirical-incubation
module load anaconda3/2023.3
conda activate llm
pip install -r requirements.txt
```

## Step 1 — Download (login node, needs internet)

**Run directly — do not submit to slurm.** Princeton compute nodes have no outbound internet, so `sbatch slurm/download.slurm` will fail. Run on a login node instead:

```bash
cd ~/empirical-incubation
module load anaconda3/2023.3
conda activate llm
export PYTHONPATH="$PWD/src:${PYTHONPATH:-}"

python -m empirical_incubation.cli download \
    --manifest manifests/memetracker.txt \
    --dest-dir /scratch/network/yh6580/empirical-incubation/raw
```

The downloader is resumable (partial files live at `<name>.part`; re-running picks up where it left off).

## Step 2 — Analyze (compute node, offline)

Parameters are hardcoded at the top of `slurm/analyze.slurm` — edit the file, then:

```bash
sbatch slurm/analyze.slurm
```

Defaults: `START=2008-08-01`, `END=2009-05-01`, `BIN_WIDTH_DAYS=1`, `MIN_TOTAL_MENTIONS=5`, `TOP_N=100`. Output goes to `$DATA_ROOT/runs/<UTC-timestamp>-<jobid>/`:

- `stages/clean/`, `stages/aggregate/`, `stages/score/` — intermediate artifacts from each stage
- `report.md` — summary, feature distributions, top-N sleeping beauties table, sanity-check sample
- `plots/<phrase-id>.pdf` — per-meme trajectories with phase shading + peak markers (≤ `TOP_N`)
- `hist_amplitude_ratio.pdf`, `hist_gap_ratio.pdf` — feature distributions across all scored phrases

### Running stages individually

Useful when tuning thresholds or re-plotting without re-aggregating:

```bash
python -m empirical_incubation.cli clean     --raw-dir RAW --out-dir STAGES/clean \
                                             --start 2008-08-01 --end 2009-05-01
python -m empirical_incubation.cli aggregate --clean-dir STAGES/clean --out-dir STAGES/aggregate \
                                             --start 2008-08-01 --end 2009-05-01 \
                                             --bin-width-days 1 --min-total-mentions 5
python -m empirical_incubation.cli score     --aggregate-dir STAGES/aggregate --out-dir STAGES/score
python -m empirical_incubation.cli report    --aggregate-dir STAGES/aggregate --score-dir STAGES/score \
                                             --out-dir REPORT --top-n 100
```

If a stage's output directory already exists, it is overwritten in place — safe to rerun.

## Tuning

The three-phase detector thresholds live in `src/empirical_incubation/detect.py:is_sleeping_beauty`:

- `min_early_amplitude` — early bump must clear this floor
- `min_amplitude_ratio` — main peak / early peak (dominance)
- `max_middle_fraction_of_main` — middle window must stay this far below the main peak (dormancy depth)

After the first real run, eyeball `report.md` + the histograms, edit the thresholds, and re-run only the last two stages against the cached `timelines.npy`:

```bash
python -m empirical_incubation.cli score  --aggregate-dir STAGES/aggregate --out-dir STAGES/score
python -m empirical_incubation.cli report --aggregate-dir STAGES/aggregate --score-dir STAGES/score \
                                          --out-dir REPORT --top-n 100
```

No need to re-parse the raw gz or rebuild the timelines matrix.
