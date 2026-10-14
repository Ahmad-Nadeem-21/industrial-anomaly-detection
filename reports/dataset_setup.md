# Dataset setup guide

Status (2026-10-14): selected dataset acquired from the user-provided root archive and safely extracted into `data/mvtec_ad`. Full image/mask integrity checks passed. Normal-only pilot progress is recorded in `reports/real_data_milestone.md`.

## Acquisition record

The user supplied `mvtec_anomaly_detection.tar.xz` (5,264,982,680 bytes), described as an official download. Its local SHA-256 is `cf4313b13603bec67abb49ca959488f7eedce2a9f7795ec54446c649ac98cd3d`. This identifies the supplied file; it is not an independently authenticated official checksum. The original archive remains unchanged at `../CS415 Final Project Archive/mvtec_anomaly_detection.tar.xz`; archive patterns are ignored by Git. It was moved during the October 14 cleanup; original-location provenance is retained in `cleanup_manifest.json`.

`scripts/extract_dataset.py` scanned all 6,880 entries and extracted only bottle, carpet, screw and top-level notices, totaling 1,093,497,764 bytes. It rejects unsafe paths, links, special entries, out-of-root destinations and file overwrites. The selected categories contain 357, 488 and 601 files respectively; category notices and top-level `readme.txt`/`license.txt` were preserved. The supplied license is CC BY-NC-SA 4.0; the supplied readme requests citation of Bergmann, Fauser, Sattlegger and Steger, CVPR 2019.

All 1,440 selected PNG images and masks decoded successfully. Training-normal counts are 209/280/320 for bottle/carpet/screw; anomalous mask counts are 63/89/119. Masks matched image dimensions, were binary and nonempty, and had no missing or orphaned pairs. This audit inspected file integrity and labels, without displaying test images or computing model scores. Details are in `dataset_acquisition.json` and `dataset_integrity.json`.

The earlier form-access blocker is resolved by the user-provided archive. Future acquisition should still use the [official original MVTec AD page](https://www.mvtec.com/research-teaching/datasets/mvtec-ad).

## Handling and validation

1. Open the [official MVTec AD page](https://www.mvtec.com/research-teaching/datasets/mvtec-ad). Select original MVTec AD. Follow its download form/instructions; do not substitute AD 2 or an unofficial mirror. The user should supply any required personal information directly.
2. Read and retain the supplied license. The site specifies [CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/), including attribution, noncommercial use and share-alike conditions for adapted material. A noncommercial course study appears consistent with that intended use, subject to the actual terms and course rules; this is not an instructor approval. Credit dataset authors in the report and mark modifications to dataset-derived figures.
3. Extract into a dedicated local data directory. Do not flatten the category folders. Preserve the archive name, retrieval date and checksum; record any official checksum if supplied. A locally computed checksum provides provenance, not independent proof of download authenticity.
4. Expect category directories such as the example below, then verify the actual downloaded archive. Check all image decodes, train/good counts, test categories, image sizes and mask correspondence. Reject corrupt files and missing anomalous masks rather than silently dropping them.

```text
mvtec_ad/
  bottle/
    train/good/*.png
    test/good/*.png
    test/<defect_type>/*.png
    ground_truth/<defect_type>/*_mask.png
  carpet/
  screw/
  ...
```

5. The implemented CLI accepts `--root` pointing to the directory containing category folders, not to train or test, and defaults to `data/mvtec_ad`. Keep machine-specific paths out of shared source files. No environment-variable override is implemented. The normal-only loader and split/hash auditor are available; a complete real-dataset integrity audit remains pending acquisition.
6. The project `.gitignore` now excludes `data/` and generated artifacts. Retain source configs, split-generation rules and small reproducibility manifests outside those ignored directories. Before extraction, enumerate archive entries and reject absolute paths, parent traversal, symlinks, hardlinks, and special files; resolve every destination beneath the dedicated extraction directory and refuse to overwrite existing files. Preserve archive checksums and supplied notices even when extracting only the three study categories.
7. Dataset auditing may check test file integrity without exposing scores or choosing algorithms from test labels. Model development uses training/calibration data and synthetic fixtures. A separate explicit evaluation command should be the only path that computes final test metrics.
8. Obtain the official evaluation code from the same dataset page if adding AUPRO. Read its README/license and compare a small synthetic example against the implementation before reporting that metric. Evaluation code has not yet been downloaded or validated.

Completed locally: isolated baseline environment, normal-only loader/auditor and synthetic fixture verification. Remaining work: acquire the dataset, validate actual contents, and run the real normal-only pilot. No real dataset audit or benchmark results exist.

## Re-extraction after cleanup

The active dataset already exists and should be reused. The extractor requires an explicit archive path and refuses an existing extraction directory or acquisition report. In a fresh project workspace, use:

```powershell
.\.venv\Scripts\python.exe scripts/extract_dataset.py --archive "../CS415 Final Project Archive/mvtec_anomaly_detection.tar.xz"
```

The course handout is retained at `../CS415 Final Project Archive/Final Project Instructions.pdf`. Historical run locations in older reports map to their preserved copies through `cleanup_manifest.json`.
