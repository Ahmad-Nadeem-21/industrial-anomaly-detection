# CS 415 Industrial Defect Detection

CPU-only study for two students. Research protocol: [research design](reports/research_design.md).
Current milestone (2026-10-14): dataset acquisition, integrity checks and all three real normal-only pixel pilots are complete. See [all milestone statuses](reports/milestone_status.md) and [verified pilot results](reports/real_data_milestone.md).
This milestone implements the standardized pixel baseline and normal-only development tools.
PaDiM, texture model, controlled final experiments and research results are not implemented yet.

## Reproduce on Windows PowerShell

Run from this project directory. Python 3.14.0 is the reference interpreter for this milestone.
The requirements pin direct dependencies; `requirements-lock.txt`, when present, records the tested complete environment.
No PyTorch installation is needed for the pixel baseline. The later PaDiM environment will be checked separately.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m defect_detection synthetic-smoke --output artifacts/synthetic_smoke
```

Use a new output directory for each run; existing runs are never overwritten. Synthetic smoke uses generated normal images with non-square dimensions. Its scores and timing are pipeline checks, **not MVTec benchmark results**. No anomalous data is used to fit or calibrate.

## Real normal-only pilot

Obtain the original MVTec AD dataset using [dataset setup](reports/dataset_setup.md).
Expected layout: `data/mvtec_ad/bottle/train/good/*.png`, with carpet and screw arranged similarly.
The following commands read only training normals. `audit` is a normal-only integrity/split audit, not a complete dataset/mask audit.

```powershell
.\.venv\Scripts\python.exe -m defect_detection audit --root data/mvtec_ad --category bottle --output artifacts/bottle_audit
.\.venv\Scripts\python.exe -m defect_detection normal-pilot --root data/mvtec_ad --category bottle --output artifacts/bottle_normal_pilot
```

Config lives in `configs/pixel.json`. The default pilot fits the entire 80% fitting pool and calibrates on the remaining 20%; select `--fraction 0.25 --seed 17` for the first nested subset. Manifests store all declared nested subsets and SHA-256 file hashes. Hashes are checked before fitting.

Outputs include resolved config, split manifest, model, original-resolution raw normal maps, calibration scores, software versions and pilot timing. Threshold is the normal calibration 95th percentile (`higher`), with strict `score > threshold` classification. Scores cannot establish defect sensitivity on normal-only data.

Pixel statistics use streaming float64 Welford moments and sample standard deviation, floored at 0.02. RGB bilinear resize produces 224x224 input; channel RMS standardized residuals are smoothed using SciPy Gaussian sigma 4, reflect padding, truncate 4, then Pillow float32 bilinear resize restores original width/height. Image score is the final map maximum. Save/load uses NPZ with pickle disabled.

Latency measures image decode, preprocessing, inference and map resize after five warm-ups, excluding writes and metric computations. These are development timing samples; CPU thread count, sampled peak RSS and separate model-only timing are pending the later resource feasibility gate.

## Evaluation boundary and tests

There is deliberately no final-test CLI in this milestone. `data.test_records` validates image/mask pairing for future evaluation and was also used for the real dataset integrity audit; it has not been used for model scoring. Normal test records carry `mask=None`, representing legitimate all-zero ground truth; a missing anomalous mask raises an error.

`metrics.ranking_metrics` computes flattened category-level AUROC and average precision, rejecting nonfinite scores and reporting `null` with a reason for single-class inputs. No per-image/test normalization occurs. Metric helpers are fixture-tested, but the memory-bounded original-resolution final evaluator remains a later milestone.

Tests cover deterministic/disjoint/nested splits, changed content hashes, variance floors, non-square maps, serialization parity, perfect/reversed/tied ranking, single-class and nonfinite scores, and missing/incorrect masks.

Data and generated artifacts are ignored by Git. No dataset is redistributed, and no global Python packages or Git settings are changed. See the dataset guide for licensing and attribution.

API references: [Python virtual environments](https://docs.python.org/3.14/library/venv.html), [scikit-learn average precision](https://scikit-learn.org/1.7/modules/generated/sklearn.metrics.average_precision_score.html).

## Local files and sharing

Active `.venv/`, `data/` and final pilot `artifacts/` stay local and are ignored by Git. The original archive, course handout and superseded runs were moved to the sibling `../CS415 Final Project Archive/`; see [cleanup record](reports/cleanup_manifest.json). Historical reports retain their original run paths, mapped by that record. Share source, configuration, tests, requirements and reports; do not upload the dataset, generated maps/models or environment. GitHub publishing is handled by the user; no remote or push has been configured by this cleanup.
