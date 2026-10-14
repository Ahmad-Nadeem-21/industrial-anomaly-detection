# Project milestone status

Updated October 14, 2026. Team: two students; laptop CPUs only. **Phases 1 and 2 are complete for the initial scope. Phase 3 is next.** Phase 5 has supporting infrastructure only; phases 3, 4 and 6 have not been implemented. The six phases below retain the original project numbering. Their effort differs substantially, so phase counts are not a completion percentage.

| Phase | Status | Implementation and evidence | Remaining work |
|---|---|---|---|
| 1. Environment, literature, dataset and research design | Complete for initial scope | Course PDF reviewed; isolated pinned baseline environment; initial primary-source research, CPU scope, dataset provenance and protocol documented. | Literature review continues; confirm weekly availability and validate the separate deep-method dependency stack in phase 3. |
| 2. Dataset inspection and classical baseline | Complete | Three categories extracted; all 1,440 PNGs decoded and masks validated. Streaming pixel baseline, deterministic splits, calibration, serialization and all three real normal pilots verified. Evidence: `baseline_milestone.md`, `real_data_milestone.md` and acquisition/integrity JSON. | This completes the initial pixel reference baseline; the planned additional local texture baseline remains unimplemented. Normal-only pilots do not establish defect sensitivity. |
| 3. Deep implementation | Not started | Compact PaDiM specification exists; no deep feature extractor or Gaussian model implementation yet. | Implement frozen pretrained features, normal fitting and inference; validate synthetic behavior, normal pilots and CPU feasibility including timing and memory. |
| 4. Controlled experiments and extension | Not started | Fractions, seeds and comparison rules are specified. | Implement the local texture extension, experiment driver and resource controls; freeze configurations; run methods across categories, fractions and seeds without test-driven tuning. |
| 5. Metrics, visualization, error analysis and reproducibility | Partial foundation only | Fixture-tested ranking helpers, deterministic manifests/content hashes, raw normal maps, saved models and environment records exist. | Build memory-bounded original-resolution final evaluation, result figures and failure analysis; measure test AUROC/AP and repeated resource behavior; complete end-to-end reproducibility. No final test model scores exist. |
| 6. Report, presentation and final verification | Not started beyond planning documents | Research design and milestone records are available; no final research report or slides. | Prepare findings, citations, limitations, individual contributions/reflections and reproducible final verification; presentation December 1/3 and report December 11. |

## Latest implementation and verification

The October 14 cleanup moved only archival materials into `../CS415 Final Project Archive/`. The original dataset archive, course PDF, four historical synthetic/verification runs and superseded first bottle pilot remain available. `cleanup_manifest.json` maps every original project-relative path to its preserved sibling location and byte count. Active data, environment, all three audit manifests and final real pilot runs remain in the project. Historical October 13 baseline report was preserved unchanged.

The extraction helper now requires `--archive PATH`, allowing the archive to live outside the project. A check using its new archive location correctly refused to overwrite the existing dataset/report. The pipeline suite passed **15 tests in 5.71 seconds** after cleanup and the CLI change. No models were retrained or tests scored for cleanup. No Git repository, remote, commit or push was created by this task; the user will publish separately.

## Next milestone

Implement the compact PaDiM method and local texture baseline, then establish CPU feasibility using normal training/calibration data before freezing the final experiment configuration. Current normal-only pilot times are development observations, not a completed resource benchmark. No final test AUROC/AP, research comparison or anomaly-sensitivity result exists yet.
