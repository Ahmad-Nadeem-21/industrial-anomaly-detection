# Real-data acquisition and normal-only pilot milestone

Date: 2026-10-14. Status: dataset acquisition/integrity and pixel-baseline normal pilots complete; final evaluation not performed.

## Implementation completed

- Safely extracted bottle, carpet and screw plus notices from the user-provided 5,264,982,680-byte archive. Original archive retained. See `dataset_acquisition.json` for local SHA-256 and provenance limitations.
- Decoded all 1,440 PNG images/masks; validated anomalous mask correspondence, dimensions, binary values and nonempty content. No orphan masks. See `dataset_integrity.json`.
- Ran normal-only audit and full-fitting-pool pixel pilot for all three categories. Manifests contain deterministic disjoint fitting/calibration splits, nested subsets and content hashes.
- All pilots verified exact saved/reloaded model output parity, produced normal calibration thresholds and maps, and reported `test_data_accessed: false`.

## Development timing samples

| Category | Fit normals | Calibration normals | Fit seconds | Median ms/image | P95 ms/image | Model bytes |
|---|---:|---:|---:|---:|---:|---:|
| bottle | 167 | 42 | 4.246 | 27.70 | 31.97 | 1,175,175 |
| carpet | 224 | 56 | 9.221 | 46.63 | 52.51 | 1,643,666 |
| screw | 256 | 64 | 5.793 | 42.56 | 53.55 | 597,987 |

These are single-run normal-only development samples, not benchmark performance. Prediction latency includes image decode, preprocessing, inference and resizing, excludes output writes, and follows five warmups. Thread controls, sampled peak RSS, separate model-only timing and repeated resource measurements remain pending. No test AUROC/AP or defect sensitivity has been measured.

Final runs are `artifacts/bottle_normal_pilot_uncontended_20261014`, `artifacts/carpet_normal_pilot_20261014`, and `artifacts/screw_normal_pilot_20261014`. Audits are `artifacts/<category>_audit_20261014`. The first run is retained at `../CS415 Final Project Archive/artifacts/bottle_normal_pilot_20261014` (original project path: `artifacts/bottle_normal_pilot_20261014`), but its timings are superseded because it overlapped dataset integrity decoding. The final bottle rerun occurred after the audit and all other pilots ended; its threshold and counts match the first run.

## Independent verification

Independent verification recomputed the archive checksum and corroborated archive/extracted byte counts and category file counts. All three manifests passed content-hash and disjoint-split checks. Six first/last calibration maps and scores matched reloaded-model predictions exactly and retained original dimensions. The test suite passed: **15 tests in 1.51 seconds**. Verification performed no test model scoring.

## Reproduction

The completed pilot output paths are shown below. Commands refuse existing output directories; use a fresh suffix when reproducing the runs. Run from the project root after the dataset has been extracted.

```powershell
.\.venv\Scripts\python.exe -m defect_detection normal-pilot --root data/mvtec_ad --category bottle --output artifacts/bottle_normal_pilot_uncontended_20261014
.\.venv\Scripts\python.exe -m defect_detection normal-pilot --root data/mvtec_ad --category carpet --output artifacts/carpet_normal_pilot_20261014
.\.venv\Scripts\python.exe -m defect_detection normal-pilot --root data/mvtec_ad --category screw --output artifacts/screw_normal_pilot_20261014
```

## Completion boundary

Completed: isolated pixel environment (prior milestone), dataset acquisition, safe extraction, integrity audit, leakage-safe normal splits, real normal-only pixel pilots.

Remaining: texture baseline and frozen-feature PaDiM, CPU resource feasibility, configuration freeze, controlled final experiments, result analysis, presentation and report. Test data were decoded only for integrity checks and never scored by a model. Pilot scores do not establish anomaly-detection quality.
