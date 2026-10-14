# Research design

Date: October 13, 2026. Status: proposed protocol; no experimental results exist.

Team: two students, laptop CPUs only. Weekly availability is not yet specified.
Planning assumption: 6-8 hours per person per week, to be revised if needed.

## Problem and contribution

Title: Industrial Visual Anomaly Detection: Comparing Classical and Deep Feature-Based Methods Under Limited Training Data.

Learn normal product appearance from defect-free images, then score previously unseen images and localize unusual regions. The primary question is how classical and pretrained deep features compare as normal training data becomes scarce. Secondary questions concern localization, category-dependent failures, runtime, and memory.

Our contribution will be a controlled CPU study, understandable implementations, reproducible splits, and evidence-backed failure analysis. We do not claim a novel anomaly detection algorithm. A negative result or a strong classical baseline is a valid finding.

Hypotheses, not findings:

- Deep features may be less sensitive to benign appearance variation than raw pixels.
- A position-independent texture model may help on textures but miss structural defects.
- Smaller training sets may hurt covariance estimation and coverage of normal variation.
- Higher localization AUROC need not imply useful precision for small defects.

## Methods and implementation order

Implement A and B end to end before C. Apply every included method to every selected category; do not choose winners separately by category after seeing tests.

### A: standardized pixel reference

Resize the complete RGB image to 224 x 224 and scale to [0,1]. Fit a separate mean and sample standard deviation at each position/channel using fitting images only. Score each pixel by the root mean squared standardized residual across channels. Use a standard-deviation floor of 0.02 intensity units, fixed before evaluation. This is our transparent sanity baseline, not a state-of-the-art claim. It assumes corresponding pixels have comparable meanings; alignment and texture phase variation may violate that assumption.

### B: compact PaDiM reproduction

PaDiM represents spatial patches with frozen pretrained CNN features, fits location-specific Gaussian distributions, and scores Mahalanobis distance. The paper uses random feature selection, covariance regularization, and multiscale ResNet features. Its R18 variant is a useful starting point [2].

Our initial configuration is ResNet18, ImageNet weights, layers 1/2/3, 100 fixed randomly selected channels, and covariance ridge 0.01. Freeze the network, use evaluation mode, and disable gradients. Only normal feature means/covariances are fitted. Persist feature indices and the exact weights identifier. Use Cholesky solves rather than explicit inverses. Keep feature selection fixed across data-fraction replicates so those replicates measure data-selection variation.

Project departures: full-image 224 x 224 resize instead of the paper's resize/crop pipeline; shared postprocessing and original-resolution evaluation below. Thus this is an adapted reproduction, not an exact reproduction of published scores. Gaussian and spatial assumptions can still fail; deep features do not guarantee alignment invariance.

### C: local texture-statistics baseline

This is a team-designed baseline using standard image operations, not a named published detector. Form three features at every location: local grayscale mean, local grayscale standard deviation, and local mean Sobel-gradient magnitude, each with a 9 x 9 window and reflect padding. Use luminance 0.299R + 0.587G + 0.114B and document Sobel normalization.

Fit feature scaling from normal fitting images, then a position-independent, single three-dimensional Gaussian over their standardized local descriptors, using ridge 0.01. Use Mahalanobis distance as the pixel map. Pool moments in chunks rather than retaining every descriptor. This tests whether discarding exact position helps accommodate normal texture variation. A single Gaussian can poorly represent multimodal textures; structural defects with familiar local appearance may be missed. We will report this limitation even if results are weak.

### Shared output processing

For A, B, and C, produce a nonnegative 224 x 224 map, apply a fixed Gaussian smoothing sigma of 4 at that resolution, then bilinearly resize to the original image dimensions. For B, first bilinearly upsample the feature-grid map to 224 x 224. Define image score as the maximum of the final original-resolution map. These common choices are experimental controls, not claims of optimality. Record them exactly and never optimize them against test labels.

Optional PatchCore uses a representative normal patch-feature bank and nearest-neighbor scoring [3]. Its bank construction and search add runtime and implementation work, so it is outside the committed scope. If attempted, distinguish a faithful coreset implementation from a simplified random-bank variant.

## Dataset and leakage protocol

Use original MVTec AD, not AD 2 or LOCO. The official source describes normal training images, mixed normal/anomalous test images, and pixel annotations [1,4]. Start with bottle, carpet, and screw to cover an object, a texture, and an additional object category. This is a declared subset study, not a full 15-category benchmark. Inspect training appearance to assess assumptions; do not select categories based on test scores.

1. Preserve official train/test boundaries and all test images for each selected category.
2. Sort train/good paths and make a fixed, seeded 80% fitting-pool / 20% calibration split per category, using split seed 415. Store explicit relative paths and file hashes. Calibration size is ceil(0.2*N); the remainder is fitting pool.
3. From the fitting pool, use nested 25%, 50%, and 100% subsets for seeds 17, 29, and 43. Size is floor(fraction*pool_size); require at least two images. Use the same subset for all methods. Fractions refer to the fitting pool, not the entire official training split. Thus 100% uses roughly 80% of the official training images for fitting.
4. Keep the same calibration set for all runs. It never contributes to means, covariance, feature scaling, or memory banks. Fix feature-selection seed to 101 for B.
5. Use normal calibration scores only to choose an illustrative image decision threshold: the empirical 95th percentile using the 'higher' quantile rule. Predict anomalous when score is strictly greater than that threshold. This is a nominal calibration target, not a guarantee of 5% future false positives, especially with few calibration samples.
6. Main metrics are threshold-free. No anomalous validation examples exist in this protocol, so normal calibration cannot establish sensitivity or select the best defect detector. Do not use it to make that claim. Do not claim calibrated pixel decisions; display continuous localization maps.
7. Finalize algorithms, categories, preprocessing, metrics, and seeds before running the test evaluator. Save a dated protocol/configuration snapshot. Use synthetic fixtures and held-out normal images for pipeline debugging. Do not inspect test heatmaps for method development.
8. Test labels/masks may be used only by final evaluation and subsequent error analysis. Any post-test methodological change must be labeled exploratory; rerunning does not restore an untouched test set.

No per-image or test-dataset min/max normalization before metrics. Use raw scores within each category. For comparable visual displays, use a fixed calibration-derived scale per run and explicitly label display clipping; saved raw maps remain unchanged.

## Experiment matrix and feasibility gates

| Stage | Methods | Categories | Fractions | Subset seeds | Purpose |
|---|---|---|---|---|---|
| Development | A, then B | bottle training/calibration only | small normal subset | 17 | Loader, maps, memory, timing; no benchmark results |
| Core | A, B | bottle, carpet, screw | 25%, 50%, 100% | 17, 29, 43 | Main data-efficiency comparison |
| Third method | C | same three | same fractions | same seeds | Classical texture comparison |
| Optional | PatchCore or more categories, not both initially | fixed before evaluation | fixed before evaluation | recorded | Only if core work is complete |

Three methods yield 81 logical experiment rows. At 100%, subset seeds produce identical fitting data. Since feature selection is fixed, these are duplicate configurations: execute only once and reference the same result in the paired curves. There are 63 distinct core configurations with C, or 42 with A/B alone. Never present duplicated 100% runs as independent evidence or a variance estimate.

Use 128 x 128 for development smoke tests only. Target 224 x 224 for the declared study; if timing requires 128, change the entire study before unlocking tests and label it reduced-resolution. Do not promise runtimes before measurement.

At 224 pixels, a 56 x 56 grid with 100 x 100 float32 covariance matrices is about 120 MiB for one covariance tensor alone. Factorization, features, model weights, and temporary allocations increase total memory. Process one category/model at a time, stream moments in manageable chunks, and avoid caching all embeddings in RAM. Frozen feature caches can reduce repeated compute, but keys must include image hash, weights, preprocessing, layer set, and selected channels. Compute fitting statistics from the selected subset only.

Feasibility gate: measure A/B on training/calibration data, project total cost, and reserve at least twice that estimate for failures/repeats. Freeze CPU thread count after a small normal-only timing check. Do not compare timing across different teammates' laptops as if hardware were identical. Prefer all timing on one reference laptop.

## Metrics, outputs, and scientific checks

Compute each category separately:

- Image AUROC: ability to rank defective above normal images; does not choose an operating threshold.
- Pixel AUROC: rank defective above normal pixels across all test images in that category, including normal images. Large numbers of background pixels can make a low false-positive rate coexist with many false alarms.
- Pixel average precision: score using the average-precision definition, not trapezoidal PR area; report anomaly pixel prevalence because AP depends on prevalence.
- Optional AUPRO@0.30: verify the official evaluator before implementation. PaDiM describes the normalized integral of mean per-region overlap over false-positive rates 0 to 0.30 [2]. Report evaluator version, connectivity, threshold handling, integration and background scope; omit this metric if parity cannot be established.
- Image sensitivity and specificity at the normal-calibrated threshold, with counts and the calibration sample size. These support false-positive/false-negative analysis, not primary model selection.
- Fit time, batch-one inference median/p95, sampled peak process RSS, and serialized model size. RSS sampling is an observed peak and may miss short spikes.

Evaluate maps against untouched original-size binary masks. Do not downsample ground truth for the main metrics. Normal test images have legitimate all-zero masks; an absent anomalous mask is an error, not permission to invent a label. Metrics must reject nonfinite scores and distinguish undefined single-class metrics from zero performance.

Average category metrics equally for macro results; do not pool scores across categories whose scales differ. Report mean and standard deviation across subset seeds for 25% and 50%, with the full per-seed values. Those seeds measure training-subset variability on a shared test set, not population uncertainty or statistical significance. The 100% row has one independent configuration. Avoid image-wise averaging of pixel AUROCs, which is undefined on normal-only images.

Time decoding + preprocessing + inference + map resize separately from model-only inference. Exclude metric computation, visualization and file writes from inference latency. Record five warm-up calls, then per-image measurements; use one CPU thread configuration, batch size one, and no concurrent experiment jobs. Record environment, warm-up policy and sample count. Feature caching must not bypass inference during latency measurement; report cold feature extraction cost separately from reused-cache fitting cost.

Save resolved config, software versions, hardware, split manifests, feature indices, timings, resource samples, per-image score/label/defect type, raw maps, and per-category metrics. Derive tables from these artifacts. Exact original-resolution pixel metrics can be memory-intensive; evaluate one category at a time with disk-backed storage if necessary, without silently substituting sampled pixels.

Critical tests: split disjointness/nesting; fixture path and mask pairing; non-square image/map alignment; hand-computable perfect/reversed/tied metric cases; normal/anomalous mask handling; constant-image variance floor; finite covariance solves when samples < dimensions; frozen batch-normalization state; save/load parity; deterministic seeds. No real test labels are needed for these tests.

After evaluation, examine highest-scoring normal images and lowest-scoring defective images, plus localization failures selected by low per-image AP on anomalous images. Include successful examples and at least one case from each category. Record defect types and example counts. Do not imply a suspected texture/alignment explanation is established without inspecting the actual images and predictions.

## Schedule and responsibilities

Dates use America/Chicago. There are 49 days to December 1 and 59 days to December 11 as of October 13. Milestones depend on the unconfirmed weekly-hours assumption.

| Dates | Deliverable and exit condition |
|---|---|
| Oct 13-18 | Agree scope, confirm course expectations, obtain dataset, choose compatible isolated environment; dataset audit passes |
| Oct 19-25 | A and data/evaluation fixtures; reproducible maps and saved normal-only smoke artifacts; begin methods writing |
| Oct 26-Nov 1 | B with fitting, serialization and resource checks; A/B pipeline verified; literature/methods draft |
| Nov 2-8 | C, experiment runner, protocol freeze; complete resource pilot before any final test run |
| Nov 9-15 | Execute controlled matrix; preserve failures/logs; generate tables directly from saved results |
| Nov 16-22 | Error analysis, justified correctness reruns, report draft and first slide outline |
| Nov 23-29 | Reproduction on second laptop, debugging buffer, finalize figures and rehearse |
| Nov 30-Dec 3 | Presentation-ready by Nov 30; present on assigned Dec 1 or Dec 3 date |
| Dec 4-10 | Report revisions, individual reflections, attribution and contribution audit; submission-ready Dec 10 |
| Dec 11 | Hard course report deadline; avoid relying on this day for remaining experiments |

Proposed ownership: student 1 leads data/A/C and experiment bookkeeping; student 2 leads B and resource measurements. Both review metrics/splits, explain both method families, write their own reflections, and rehearse. These are suggested roles, not claims about work performed. Keep a dated contribution log and hold two brief coordination meetings weekly. Reserve roughly 25% of effort for debugging, integration and writing rather than adding methods.

Minimum viable research outcome: verified A/B implementations, all three declared categories, the 25/50/100% comparison, saved metrics/maps/resource evidence, honest limitations and a reproducible report. Target C to reach three distinct detectors. PatchCore, all 15 categories and extra backbone studies are optional. The course PDF itself does not mandate three algorithms; confirm that a limited-data extension with two detectors meets the instructor's expectations if C must be dropped.

For two students the course minimum is 10 double-spaced report pages. Suggested sections: problem and personal motivation; related work; methods; protocol; results; error analysis; limitations/future work; individual reflections and contributions; references. Presentation figures: pipeline, one method-comparison table, data-fraction curves, representative heatmaps, and one explained failure.

## Decisions and next milestone

No additional permission is needed for routine local implementation within the requested project. Before experiments, confirm weekly availability and the team's proposed ownership. Seek instructor feedback on topic/scope, subset evaluation and any course-specific AI-assistance rules; the supplied PDF does not state such a policy. Dataset use must follow its terms, and no acceptance or form submission has been made on the user's behalf.

Next implementation milestone: isolated compatible environment, dataset configuration/audit, tiny synthetic loader/metric fixtures, and A. Do not build the whole project at once. Baseline package versions are now pinned in requirements.txt and validated in the local isolated environment; the later deep-method stack remains undecided; do not alter global Python or add a global Git ownership exception.

## References

[1] Paul Bergmann, Michael Fauser, David Sattlegger, Carsten Steger. MVTec AD - A Comprehensive Real-World Dataset for Unsupervised Anomaly Detection. CVPR, 2019. https://www.mvtec.com/fileadmin/Redaktion/mvtec.com/company/research/datasets/mvtec_ad.pdf

[2] Thomas Defard, Aleksandr Setkov, Angelique Loesch, Romaric Audigier. PaDiM: a Patch Distribution Modeling Framework for Anomaly Detection and Localization. arXiv:2011.08785, 2020. https://arxiv.org/abs/2011.08785 (method text: https://arxiv.org/html/2011.08785v1).

[3] Karsten Roth, Latha Pemula, Joaquin Zepeda, Bernhard Scholkopf, Thomas Brox, Peter Gehler. Towards Total Recall in Industrial Anomaly Detection. CVPR, 2022, pp. 14318-14328. https://openaccess.thecvf.com/content/CVPR2022/html/Roth_Towards_Total_Recall_in_Industrial_Anomaly_Detection_CVPR_2022_paper.html . Authors' implementation: https://github.com/amazon-science/patchcore-inspection . No code has been copied.

[4] MVTec. Official MVTec AD dataset and evaluation-code access page. Accessed October 13, 2026. https://www.mvtec.com/research-teaching/datasets/mvtec-ad

[5] Creative Commons. Attribution-NonCommercial-ShareAlike 4.0 International. https://creativecommons.org/licenses/by-nc-sa/4.0/
