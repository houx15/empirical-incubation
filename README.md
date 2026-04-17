# empirical-incubation

Detect **sleeping-beauty** patterns — an *early bump → dormancy → late explosion* shape — in mention-count time series such as SNAP MemeTracker quotes.

The detector is stricter than the standard Ke et al. (2015) beauty coefficient: it requires a visible early rise, a genuinely quiet middle phase, and a late peak that dominates the early one.

## Layout

```
src/empirical_incubation/   package (download, parse, detect, plot, report, pipeline, cli)
tests/                      pytest suite — 23 tests, all driven by synthetic fixtures
manifests/memetracker.txt   9 SNAP MemeTracker9 URLs (2008-08 .. 2009-04)
slurm/analyze.slurm         offline analysis job (no network needed)
slurm/download.slurm        kept for reference only — do NOT submit (compute nodes are offline)
pyproject.toml              local dev (uv)
requirements.txt            cluster (conda llm env)
```

Outputs are written under `$DATA_ROOT` (default `/scratch/network/yh6580/empirical-incubation/`) and are **never** committed to this repo.

## Local setup

```bash
uv sync
uv run pytest            # 23 passed
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

The downloader is resumable (partial files live at `<name>.part`; re-running picks up where it left off). ~9 files, ~a few GB total.

## Step 2 — Analyze (compute node, offline)

Parameters are hardcoded at the top of `slurm/analyze.slurm` — edit the file, then:

```bash
sbatch slurm/analyze.slurm
```

Defaults: `START=2008-08-01`, `END=2009-05-01`, `BIN_WIDTH_DAYS=1`. Output goes to `$DATA_ROOT/runs/<UTC-timestamp>-<jobid>/` with:

- `report.md` — summary, feature distributions, top-N sleeping beauties, sanity-check plots
- `plots/<id>.pdf` — per-meme trajectories with phase shading + peak markers
- `hist_amplitude_ratio.pdf`, `hist_gap_ratio.pdf` — feature distributions

## Tuning

The three-phase detector thresholds live in `src/empirical_incubation/detect.py:is_sleeping_beauty`:

- `min_early_amplitude` — early bump must clear this floor
- `min_amplitude_ratio` — main peak / early peak (dominance)
- `max_middle_fraction_of_main` — middle window must stay this far below the main peak (dormancy depth)

After the first real run, eyeball `report.md` and tune these against the observed distributions.

## CLI reference

```
python -m empirical_incubation.cli download --manifest FILE --dest-dir DIR
python -m empirical_incubation.cli analyze  --raw-dir DIR --out-dir DIR \
                                            --start YYYY-MM-DD --end YYYY-MM-DD \
                                            [--bin-width-days N]
```
