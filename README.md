# Factor models for multi-omics integration

Python practicals for the VIB 2026 course, aimed at computational biologists with basic statistics and molecular data literacy. No previous Bayesian modelling experience is assumed.

The teaching centres on a family of multi-omics factor models pioneered by **MOFA**, with MOFA+, MEFISTO, MuVI and MOFA-FLEX providing complementary approaches to sharing information, structured variation and prior knowledge. We fit models directly with **MOFA-FLEX**, and connect the workflow to **mc-ASTRA**. PCA provides the starting point for understanding scores, weights and reconstruction.

## The practical strategy

**When and why do joint factor models help us understand biological variation across molecular modalities and populations?**

Two fictional institutes on Asteron and Borealis study the same disease. Each measures RNA and protein from healthy and affected inhabitants. Planets are **groups** of different people; RNA and protein are **views** measured in aligned people within each planet. Every practical uses the same reproducible experiment: 80 Asteron inhabitants, 72 Borealis inhabitants, 90 RNA features and 60 protein features.

We begin by seeing how hidden biological and technical processes generate the measurements. We then build a representation of one table, explore probabilistic assumptions and fitting choices, and discover why independently fitted representations are difficult to compare. Only then do we integrate modalities and populations. The aim is to interpret what a model captures, what its assumptions contribute and what remains ambiguous.

Open the notebooks in this order and run their cells from top to bottom:

| Notebook | Question and role in the progression |
|---|---|
| [01 · Simulating interplanetary omics](notebooks/01_Simulating_Interplanetary_Omics.ipynb) | What processes could generate the four tables? Inspect true activities, feature patterns, contributions and noise before fitting anything. |
| [02 · PCA: one planet, one view](notebooks/02_PCA_One_Planet_One_View.ipynb) | Can a few axes summarize Asteron's RNA? Connect sample scores, feature loadings, explained variance, reconstruction and residuals. |
| [03 · Probabilistic factor analysis](notebooks/03_Probabilistic_Factor_Analysis.ipynb) | What changes when we specify a likelihood and priors? Fit MOFA-FLEX on the same RNA table, then compare learning rates and dense versus sparse weight priors. |
| [04 · Independent analyses](notebooks/04_Independent_Analyses.ipynb) | What happens when each institute analyses each modality separately? Compare all four representations while accounting for arbitrary signs, factor order and rotations. |
| [05 · Multiview within Asteron](notebooks/05_Multiview_One_Planet.ipynb) | Does integrating RNA and protein help? Fit common sample factors with view-specific weights and compare against the independent analyses, including cases where integration helps little. |
| [06 · Multigroup across planets](notebooks/06_Multigroup_Two_Planets.ipynb) | Which patterns are shared and which activities differ? Compare independent, pooled and explicitly grouped multiview models, considering centering, cohort composition and technical effects. |

Use the prediction and discussion prompts to interpret each result before moving on. Scores describe inhabitants; weights describe feature contributions. A dominant component need not describe disease, a sparse solution need not be more correct, and a shared factor does not establish a shared causal mechanism. Across planets, compare compatible feature patterns and group summaries rather than pairing different inhabitants.

## Before the course: install and check

You need an internet connection for installation, **Git**, and **Python 3.12** or **uv**. Fits use the CPU; no GPU or external dataset is needed. Install everything before attending, including mc-ASTRA's dependencies.

1. Install [Git](https://git-scm.com/downloads) if needed, and [uv using its official instructions](https://docs.astral.sh/uv/getting-started/installation/).
2. Get the course repository and create its environment:

   ```bash
   git clone https://github.com/roramirezf/FactorModels_training.git
   cd FactorModels_training
   uv venv --python 3.12.8
   uv pip install --python .venv -r requirements.txt
   ```

   uv can download the requested Python version. The included [requirements.txt](requirements.txt) pins the running environment, including exact MOFA-FLEX and mc-ASTRA Git revisions. Use this file rather than installing their latest releases; these notebooks use a development API.

3. Activate the environment:

   macOS / Linux:

   ```bash
   source .venv/bin/activate
   ```

   Windows PowerShell:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

4. Check the installation, register the notebook kernel and open JupyterLab:

   ```bash
   python -c "import mofaflex, mc_astra; print('MOFA-FLEX:', mofaflex.__version__); print('Course imports OK')"
   python -m ipykernel install --sys-prefix --name mofa-course --display-name "Python (MOFA course)"
   python -m jupyterlab
   ```

   Select **Python (MOFA course)** and run notebook **01** as your pre-course check. Later, activate the same environment and run `python -m jupyterlab` again. If using VS Code, select the repository's `.venv` interpreter for the notebooks.

These commands follow uv's [virtual environment workflow](https://docs.astral.sh/uv/pip/environments/). If PowerShell blocks activation, use `.venv\Scripts\python.exe` in place of `python` in step 4; activation is not necessary when calling the environment's Python directly.

### Alternative: Python's built-in venv, without uv

With Python 3.12 already installed, replace step 2's two uv commands with:

```bash
python3.12 -m venv .venv
```

On Windows, use `py -3.12 -m venv .venv`. Activate it as in step 3, then install:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Continue with step 4. Both installation routes use the same requirements file.

## Data, execution and reproducibility

- [notebooks/course_utils.py](notebooks/course_utils.py) contains the simulation, data access and plotting helpers. It is imported directly; there is no separate course package to install.
- `data/observed/` contains the four canonical AnnData tables. `data/teacher/` keeps the true factors, weights, contributions and noise separate from fitting inputs. [data/provenance.json](data/provenance.json) records the simulation specification. All six notebooks reuse these data without retuning the simulation.
- Fits write small score, weight and diagnostic summaries to `results/`. Run **04 before 05 and 06**, which read its summaries. Executed notebook outputs are retained for reference; running the cells performs the fits again.
- Run notebooks from the repository root or its `notebooks/` directory. No credentials, real patient data or further downloads are needed after installation.

To execute all six notebooks automatically from fresh kernels after activating the environment and registering the kernel:

```bash
python run_notebooks.py
```

The runner stops on errors, refreshes notebook outputs and records results in [validation.json](validation.json). A socket-free alternative, used in the managed validation environment, is `python run_notebooks.py --inprocess`; it starts a separate Python process and fresh in-process IPython kernel for each notebook. Standard Jupyter kernel transport has not been tested in that environment.

### Verified running versions and limits

The local running environment is **Python 3.12.8 on macOS ARM64**. The complete dependency snapshot is in `requirements.txt`, with key versions and source revisions recorded in [environment_verified.json](environment_verified.json):

| Package | Running version / revision |
|---|---|
| MOFA-FLEX | `0.2.0rc2.dev16+g2710274b7`, commit `2710274b758b1c6c4971da46590eaf724fa611a2` |
| mc-ASTRA | `0.1.0`, commit `545a90bff5e961427e61f6a03c29b25bf301b59f` |
| AnnData / MuData | `0.13.4` / `0.4.1` |
| NumPy / pandas / SciPy | `2.5.4` / `3.1.0` / `1.18.1` |
| PyTorch / scikit-learn / matplotlib | `2.15.0` / `1.9.1` / `3.10.9` |
| JupyterLab / ipykernel | `4.6.5` / `7.4.0` |

The installed environment passes `uv pip check`. Installation on Linux and Windows has not been verified; the full dependency snapshot comes from macOS. A new download and installation of every dependency was not repeated during repository preparation.

The installed MOFA-FLEX supports real groups through `fit(..., group_by='planet')`, with group-specific sample factors and shared feature weights within each view. Grouped and pooled models also differ in preprocessing; grouping is not automatic batch correction. The current notebook 06 additionally changes priors and explores a larger factor count, so its comparisons do not isolate grouping alone. Its narration walks through these configuration changes and identifies which fitted objects each comparison uses. Exact APIs, notebook configuration notes and validation details are recorded in [AUDIT.md](AUDIT.md).

## Required reading

Read all four factor-model papers below and the mc-ASTRA material. Local copies in `Papers/` are ignored by Git to keep the repository small; the online links provide access without committing PDFs. Together these readings provide context for the MOFA-pioneered family of multi-omics factor models explored in these practicals; not every extension is fitted in the core notebooks.

- **MOFA+** — Argelaguet et al. (2020), *MOFA+: a statistical framework for comprehensive integration of multi-modal single-cell data*. [Article](https://doi.org/10.1186/s13059-020-02015-1). Focus on views, groups and shared representations.
- **MOFA-FLEX** — Qoku et al., *MOFA-FLEX: A Factor Model Framework for Integrating Omics Data with Prior Knowledge*. [Preprint](https://doi.org/10.1101/2025.11.03.686250). Focus on model construction, priors and approximate inference. [Official documentation](https://mofaflex.readthedocs.io/) · [Source](https://github.com/bioFAM/mofaflex).
- **MEFISTO** — Velten et al. (2022), *Identifying temporal and spatial patterns of variation from multimodal data using MEFISTO*. [Article](https://doi.org/10.1038/s41592-021-01343-9). Focus on extending factor models to structured sample relationships.
- **MuVI** — Qoku & Buettner (2023), *Encoding Domain Knowledge in Multi-view Latent Variable Models: A Bayesian Approach with Structured Sparsity*. [Paper](https://proceedings.mlr.press/v206/qoku23a.html). Focus on structured sparsity and feature-set knowledge.
- **mc-ASTRA** — Read the [overview](https://saezlab.github.io/mc-astra/) and the tutorials on [factor analysis with MOFA](https://saezlab.github.io/mc-astra/notebooks/GetStarted_MOFA/) and [experimental groups](https://saezlab.github.io/mc-astra/notebooks/GetStarted_groups/). Connect sample representations and downstream interpretation to this course's simpler sample-level experiment. [Source](https://github.com/saezlab/mc-astra).

For the original foundation, see Argelaguet et al. (2018), [*Multi-Omics Factor Analysis—a framework for unsupervised integration of multi-omics data sets*](https://doi.org/10.15252/msb.20178124).
