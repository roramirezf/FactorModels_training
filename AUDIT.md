# Repository preparation and API checks

Prepared on 22 November 2026 from the existing course workspace. Notebooks 01–06 and `course_utils.py` were copied with their source cells unchanged. Execution refreshes outputs only. The lecture notebook and previous archives are outside this repository update.

## Evidence examined

Inventoried the four supplied PDFs in `Papers/` and inspected their first pages and metadata. All four are required reading in the README, together with mc-ASTRA. Examined the fitting, MuData and conversion cells in `GetStarted_MOFA`, `GetStarted_groups` and `GetStarted_FunctionalViews` from the original `ExampleNotebooks/` directory. The examples themselves are not required to run these practicals.

Checked the actual installed versions and the Git commit records for MOFA-FLEX and mc-ASTRA. Inspected `mf.terms.MofaFlex` and its model's `fit` signature locally: Normal, SpikeSlab and Horseshoe weight priors, PCA/random initialization, `lr`, Gaussian likelihoods, CPU execution and `group_by` are available. The notebooks' fitting calls remain visible rather than being replaced by a new abstraction.

Official reference material: [MOFA-FLEX source](https://github.com/bioFAM/mofaflex), [mc-ASTRA documentation](https://saezlab.github.io/mc-astra/), and uv's [installation](https://docs.astral.sh/uv/getting-started/installation/) and [environment](https://docs.astral.sh/uv/pip/environments/) instructions. The pinned installed source takes precedence over documentation for other versions.

## Learning outcome and execution map

| Notebook | Source / concept | Calls and expected output | Check |
|---|---|---|---|
| 01 | MOFA-style generative decomposition | Canonical AnnData and separately stored truth; activity, weight, contribution and noise figures | Saved observations match deterministic generation and signal + intercept + noise |
| 02 | PCA geometry and low-rank reconstruction | `PCA`, scores, components, variance fractions and residuals | Notebook assertions on factor and cumulative reconstruction R² |
| 03 | MOFA-FLEX probability model and priors | Normal baseline, learning rates .005/.02/.05, SpikeSlab comparison, two-seed diagnostics | Execute every configuration, inspect loss, scores, weights and reconstruction |
| 04 | Independent representations and identifiability | Four separate SpikeSlab/PCA-initialized fits; within-planet score and across-planet weight comparisons | Sample/feature alignment, exported summaries and complete execution |
| 05 | MOFA multiview sharing | Shared factors and separate view weights; per-view R²; mc-ASTRA conversion | Explicit sample reordering, comparisons to 04 and conversion assertions |
| 06 | MOFA+ group/view organization and installed MOFA-FLEX API | Independent summaries, pooled fit and `group_by='planet'`; group/view R² and truth diagnostics | Real grouped return values, common feature IDs and complete execution |

## Preserved configuration caveats

Notebook 06's pooled fit uses six factors, Horseshoe weights and lr .001. Its initial grouped fit uses six factors and SpikeSlab weights at that learning rate; a later fit explores 15 factors with Horseshoe weights. Consequently the displayed strategies are not a controlled experiment changing only grouping. The notebook also mutates its local `FIT` dictionary. Each notebook runs in a fresh kernel, so this mutation does not carry into earlier practicals. Sources and narration were deliberately preserved pending the requested editing round.

The simulation uses common weights across planets, activity differences, a technical score component and explicit intercepts. Group-wise centering removes group means; residual within-group variability and population mean differences have distinct interpretations. True scores and weights are not supplied to unsupervised fitting.

## Validation scope

`requirements.txt` contains the full 242-package environment snapshot, with exact development commits. Versions were compared against the running environment and `uv pip check` passed. `environment_verified.json` records the inspected Python version, platform, principal versions and source revisions. A full fresh dependency download/install and other operating systems were not tested during this update.

Run `python run_notebooks.py` after installing the registered `mofa-course` kernel, or `python run_notebooks.py --inprocess` for fresh processes and socket-free kernels. The latter is the available validation route in the managed workspace. Both stop on cell errors and record computation measurements in `validation.json`; neither measures classroom teaching time. No per-unit teaching timings are prescribed in the README.

All six packaged notebooks passed the fresh-process, in-process-kernel route. Total measured notebook execution was 127.05 seconds on macOS ARM64, with one PyTorch CPU thread for fitting; CPU model and RAM were not recorded. Per-notebook measurements and executed cell counts are in `validation.json`. The copied observations were checked against deterministic generation and exact signal + intercept + noise reconstruction. All 242 requirements match installed versions or source commits, notebook source cells match the originals, and local Markdown links resolve. An offline install dry-run could not fetch uncached Git sources, so it does not verify a fresh installation.

## Narration revision

At the instructor's request, revised only Markdown cells in notebooks 01–06 to support a guided walkthrough. Each code cell now has an introduction explaining its purpose, the data or fitted model in use, and the relevant helper's inputs, calculations and outputs. Fitting sections repeat the sample/view selection, factor count, priors and important optimisation choices. Plot selection, scaling, score-space comparisons, teacher diagnostics and exported summaries are explained where used rather than left implicit.

Notebook 06 explicitly identifies the different pooled/grouped prior configurations, the persistent learning-rate assignment and the distinction between the later 15-factor `group_model` object and the earlier six-factor `z_groups` tables. Existing grouped score panels labelled “Pooled coordinates” in code are identified correctly in the preceding prose; their code and titles were left untouched. Fixed numerical interpretations in 03 and 05 were replaced with prompts to inspect current outputs.

Validation of this revision compared before/after fingerprints of every complete code cell, including outputs and execution counts, and checked notebook metadata and `course_utils.py`: all are unchanged. Notebook schemas and local links pass, and each code cell is preceded by nonempty explanatory Markdown. Models were not rerun for this Markdown-only revision; the previous execution results remain applicable to the unchanged code.
