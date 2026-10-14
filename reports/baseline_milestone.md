# Baseline implementation milestone

Date: October 13, 2026 (America/Chicago).

## Milestones and completion

| Milestone | Implementation | Completion evidence |
|---|---|---|
| Research design | CPU study, A/B/C definitions, leakage protocol | Design documentation complete; final experiment freeze remains later |
| Isolated baseline environment | Python 3.14.0 `.venv`, pinned direct and complete dependency files | Installation succeeded; `pip check` passed |
| Data and reproducibility infrastructure | PNG integrity checks, SHA-256 manifests, fixed calibration and nested fitting subsets, mask pairing helper | Synthetic fixture tests passed; real dataset audit pending |
| Pixel baseline | Streaming sample moments, variance floor, map postprocessing, safe NPZ save/load | Synthetic smoke complete with exact reload parity |
| Metric foundation | AUROC/AP, finite-score validation, single-class null results | Hand-computable synthetic fixtures passed; final evaluator pending |
| Real data pilot | Ready `audit` and `normal-pilot` commands | Blocked on obtaining original MVTec AD through official access process |
| Deep/texture methods and experiments | Not started in this implementation milestone | Pending |
| Analysis, report and presentation | Design and reproduction documentation only | Research findings and submission artifacts pending |

Completion is reported by exit conditions, not an unsupported project percentage.

## Verified commands and artifacts

The isolated environment install initially hit restricted network access. A bounded escalation installed packages only inside `.venv`; no global Python modifications were made.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pip freeze | Set-Content -Encoding ascii requirements-lock.txt
.\.venv\Scripts\python.exe -m defect_detection synthetic-smoke --output artifacts/synthetic_smoke
```

Initial implementation verification: 7 tests passed in the isolated environment; no broken requirements found. The final independent verification below supersedes this initial count while retaining the original smoke record for provenance.

Synthetic artifacts are under `artifacts/synthetic_smoke/run/`: configuration, split hashes, model, calibration scores, eight original-resolution maps, and machine-readable summary. Forty generated non-square normal images produce 32 fitting and 8 calibration images at 224x224 model resolution. Save/load map equality passed. No real test images, masks, scores or heatmaps were accessed.

Observed **synthetic-only** timing: fit 0.470 s; median complete inference 0.0229 s; p95 0.0469 s over eight images after five warm-ups. Serialized model: 260,308 bytes. These tiny generated images do not estimate real MVTec throughput or detection performance. CPU thread freeze, sampled peak RSS, model-only timing and real normal-image feasibility measurements remain pending.

The full environment is recorded in `requirements-lock.txt`. PyTorch and torchvision are deliberately deferred to the PaDiM milestone; baseline environment success is not evidence of their compatibility.

## Final independent verification

After review corrections, the isolated environment passed **15 tests in 2.14 seconds** and `pip check` reported no broken requirements. Regression coverage now includes analytically known sample variance, non-square defect localization, invalid image sizes, altered manifest membership, duplicate/empty subsets, and redirected training directories. Training images are fully decoded; training paths and manifests reject redirection or test-path injection. Test image/mask discovery also checks category containment.

An independent verifier ran the following fresh synthetic checks:

| Check | Artifact directory | Verified outcome |
|---|---|---|
| Full fitting-pool smoke | `artifacts/independent_verification_smoke/run/` | 32 fitting images, 8 calibration images |
| Normal-only audit of the same fixture | `artifacts/independent_verification_audit/` | Matching manifest and 40 verified image hashes |
| 25% fitting subset, seed 17 | `artifacts/independent_verification_quarter/` | 8 fitting images, the same 8 calibration images |

All three manifests matched. All **16 saved maps and their scores** across the two pilots matched both loaded models and freshly refitted models exactly. Every saved map retained the fixture's original `(48, 80)` height/width. Resolved configurations and summaries matched the selected fractions and counts. These are synthetic pipeline checks, not research results; no real dataset was accessed.

Anti-pattern review searched for unfinished placeholders, swallowed exceptions, unsafe loading, unseeded randomness, test access and score normalization. No fabricated benchmark results, test-score normalization, or pickle-enabled model loading were found. Resource instrumentation, general configuration-schema validation and the final evaluator remain pending. This milestone supplies normal-only auditing, not a completed full-dataset audit.

## Next exit conditions

1. Obtain official dataset locally; validate normal images and persist category manifests.
2. Run the real normal-only pixel pilot and inspect resource feasibility.
3. Implement/test the compact PaDiM method and frozen pretrained feature extraction.
4. Finish texture baseline, experiment runner and full original-resolution evaluator; freeze the protocol before real test evaluation.

README contains exact reproduction commands and current limitations. No commits, pushes, final research results, or claims of completed course submission are made.

Next-phase handoff: use the tested `.venv` and `--root` dataset argument documented in README (default `data/mvtec_ad`; no environment-variable override). Follow `reports/dataset_setup.md` for official acquisition, then run fresh per-category normal audits and pilots. Preserve the training/calibration boundary and defer real test scoring until all methods, resource settings and evaluation configuration are frozen. No local repository or remote is configured, so no commit or push was attempted.
