# llm-distil-loop Setup Checklist

Use this when integrating the LLM → ML distillation loop into a new project.

---

## Prerequisites

- [ ] GitHub Copilot (agent mode) or equivalent AI IDE is available
- [ ] Confirm `.github/prompts/` directory exists (create if not)
- [ ] Python environment available
- [ ] Install MLflow: `pip install mlflow`

---

## Option A: Integrate with Kiro SDD (recommended)

### Step 1: Copy prompt files

- [ ] Copy `github/prompts/kiro-ml-distill-loop.prompt.md` into `.github/prompts/`
- [ ] Copy `github/prompts/kiro-ml-accuracy-verify.prompt.md` into `.github/prompts/`

```bash
cp github/prompts/kiro-ml-distill-loop.prompt.md    .github/prompts/
cp github/prompts/kiro-ml-accuracy-verify.prompt.md .github/prompts/
```

### Step 1b: Copy the rules file (Kiro auto-loads from `.kiro/settings/rules/`)

- [ ] Copy `kiro/settings/rules/ml-distillation-rules.md` into `.kiro/settings/rules/`

```bash
cp kiro/settings/rules/ml-distillation-rules.md .kiro/settings/rules/
```

> This file declares the non-negotiable rules (no empty reason, no sample-specific code, etc.) that govern every loop iteration. Kiro reads it automatically as a project rule.

### Step 2: Copy schema and test templates

- [ ] Copy `templates/ml-schema.md` to `.kiro/settings/templates/`
- [ ] Copy `templates/ml-test-checklist.md` to `.kiro/settings/templates/`

```bash
cp templates/ml-schema.md         .kiro/settings/templates/
cp templates/ml-test-checklist.md .kiro/settings/templates/
```

---

## Option A2: Integrate with GitHub SpecKit (specify CLI)

Use this option if your project uses [GitHub SpecKit](https://github.com/as-we/prior-art-investigation) instead of Kiro SDD.

### Step 1: Copy prompt files

- [ ] Copy `github/prompts/kiro-ml-distill-loop.prompt.md` into `.github/prompts/`
- [ ] Copy `github/prompts/kiro-ml-accuracy-verify.prompt.md` into `.github/prompts/`

```bash
cp github/prompts/kiro-ml-distill-loop.prompt.md    .github/prompts/
cp github/prompts/kiro-ml-accuracy-verify.prompt.md .github/prompts/
```

### Step 1b: Copy the rules file (add to copilot-instructions.md or steering)

- [ ] Append `kiro/settings/rules/ml-distillation-rules.md` to `.github/copilot-instructions.md`
  or copy to `.kiro/steering/ml-distillation-rules.md` if using Kiro steering

```bash
cat kiro/settings/rules/ml-distillation-rules.md >> .github/copilot-instructions.md
```

### Step 2: Copy schema and test templates

- [ ] Copy `templates/ml-schema.md` to `.specify/templates/` or `docs/`
- [ ] Copy `templates/ml-test-checklist.md` to `.specify/templates/` or `docs/`

```bash
cp templates/ml-schema.md         .specify/templates/
cp templates/ml-test-checklist.md .specify/templates/
```

### Step 6 (SpecKit): Add to AGENTS.md

Add to your project's `AGENTS.md` so the AI knows when to invoke these loops:

```markdown
## ML Accuracy Loop (for tickets involving LLM → ML distillation)
- `/kiro-ml-distill-loop` — collect LLM inference data → train → evaluate (4-step loop)
- `/kiro-ml-accuracy-verify` — human-label-based root cause analysis → generic fixes (5-step loop)
```

> Fill in `ml-schema.md` during the design phase. Keep it synchronized with your training scripts.  
> `ml-test-checklist.md` gates each training iteration — run all applicable checks before calling the loop done.

### Step 3: Replace placeholders

Replace `[PLACEHOLDER]` values in `kiro-ml-distill-loop.prompt.md`:

| Placeholder | Replace with |
|-------------|-------------|
| `[ML_FRAMEWORK]` | Framework matching your task type (e.g., `LightGBM`) |
| `[LLM_RESULTS_DIR]` | Directory where LLM inference results are saved |
| `[DATASET_PATH]` | Directory for prepared training datasets |
| `[MODEL_OUTPUT_PATH]` | Directory for trained model artifacts |
| `[EXPERIMENT_NAME]` | MLflow experiment name |
| `[TICKET_ID]` | Your project ticket prefix (e.g., `FEAT`, `ML`) |
| `[MODEL_NAME]` | Model identifier (e.g., `intent_classifier`) |

Replace `[PLACEHOLDER]` values in `kiro-ml-accuracy-verify.prompt.md`:

| Placeholder | Replace with |
|-------------|-------------|
| `[VERIFIED_DIR]` | Directory for human-verified ground-truth samples |
| `[TARGET]` | Accuracy target (e.g., `0.80`) |

> The `scripts/` commands in the prompts are illustrative. Implement or adapt them to match your project structure.

### Step 4: Implement required scripts

The prompts reference a set of project scripts by convention. These are **not provided** by this package — implement them in your project to match your stack and directory layout.

| Script convention | Required interface |
|------------------|-------------------|
| LLM schema validator | `python scripts/validate_schema.py --input <llm_results_dir>/` — exits non-zero on schema violations |
| Dataset preparer | `python scripts/prepare_dataset.py --llm-results <dir> --output <dataset.csv>` — joins LLM output with features |
| Model trainer | `python scripts/train_model.py --dataset <csv> --model-output <dir>` — trains and saves model artifact |
| Data stats | `python scripts/data_stats.py --dataset <csv>` — prints class distribution and missing rates |
| Quality gate | `python scripts/quality_gate.py --model <dir>` — runs tests + accuracy check, exits non-zero on failure |
| Comparison | `python scripts/compare_accuracy.py --all-verified <dir>` — prints F1 vs human-verified samples |
| Verify CLI | `python scripts/verify.py add --sample-id <id> --correct-label <label>` — registers human-labeled sample |
| Accuracy logger | `python scripts/save_accuracy_log.py --ticket <id> --ml-f1 <f> --llm-f1 <f> --api-cost <usd>` — appends to log |

> These scripts are illustrative; adapt names and paths to your project.  
> A minimal PoC can start with a single Jupyter notebook covering steps 1–3 before extracting scripts.

### Step 5: Select ML framework

See the Framework Selection table in `README.md`:

- [ ] Determine task type (Tabular / NLP / Audio / Image / Video / Audio Features→Tabular)
- [ ] Narrow down student model candidates
- [ ] Replace `[ML_FRAMEWORK]` in `kiro-ml-distill-loop.prompt.md`

### Step 6: Add to AGENTS.md (optional)

Add to your project's `AGENTS.md` so the team knows when to invoke these loops:

```markdown
## ML Accuracy Loop (for tickets involving LLM → ML distillation)
- `/kiro-ml-distill-loop` — collect LLM inference data → train → evaluate (4-step loop)
- `/kiro-ml-accuracy-verify` — human-label-based root cause analysis → generic fixes (5-step loop)
```

---

## Option B: Standalone (no Kiro / cc-sdd)

- [ ] Copy `github/prompts/kiro-ml-distill-loop.prompt.md` to your project's `.github/prompts/`
- [ ] Copy `github/prompts/kiro-ml-accuracy-verify.prompt.md` to your project's `.github/prompts/`
- [ ] Replace all `[PLACEHOLDER]` values (same as Step 3 above)
- [ ] Copy `templates/ml-schema.md` to `docs/` or your project's spec folder
- [ ] Copy `templates/ml-test-checklist.md` to `docs/` or your project's spec folder
- [ ] Reference `kiro/settings/rules/ml-distillation-rules.md` in your contribution guide
- [ ] Implement the 8 required scripts per the interface table in Step 4 above

---

## Verification

- [ ] `kiro-ml-distill-loop.prompt.md` exists in the prompts folder
- [ ] `kiro-ml-accuracy-verify.prompt.md` exists in the prompts folder
- [ ] `ml-distillation-rules.md` exists in `.kiro/settings/rules/` (or referenced in contribution guide)
- [ ] All `[PLACEHOLDER]` values replaced with project-specific values
- [ ] `ml-schema.md` filled in: input features, LLM output schema, and model interface
- [ ] `ml-test-checklist.md` passes on PoC scale (50–100 samples)
- [ ] Required scripts implemented (or PoC notebook covers the pipeline end-to-end)
- [ ] MLflow installed and `mlflow ui` launches successfully
