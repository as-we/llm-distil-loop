---
description: "Run 4-step LLM → ML distillation loop: generate labels → prepare data → train → validate accuracy"
---

# LLM → ML Distillation Loop

> Use a frontier LLM as teacher to generate labeled training data, then distill that knowledge into a lightweight ML model for low-latency, low-cost production inference.
>
> **Rules enforced** (from `ml-distillation-rules.md`):
> - Samples with empty `reason` field are rejected unconditionally
> - No sample-specific special-casing in code
> - Human review required before closing any iteration
> - Accuracy must be logged every iteration

## User Input

```text
$ARGUMENTS
```

You **MUST** consider user input before proceeding (e.g., ticket ID, ML framework, target accuracy).

## Pre-Execution: Read Project Schema

Before starting, check for the ML schema file in this order:
1. `.specify/templates/ml-schema.md`
2. `.kiro/settings/templates/ml-schema.md`
3. `docs/ml-schema.md`

If found, read it and use the defined `[LLM_RESULTS_DIR]`, `[DATASET_PATH]`, `[MODEL_OUTPUT_PATH]`, `[ML_FRAMEWORK]`, and `[TARGET]` values.  
If not found, ask the user for these values before proceeding.

---

## Step 1: LLM Inference — Generate Labeled Data

1. Acquire input samples from the dataset
2. Run LLM inference — pass inputs to the LLM teacher; collect structured JSON output
   - **Required**: Output must include a `reason` field (chain-of-thought reasoning)
   - Reject samples with empty/missing `reason` — do not include in training data
3. Store results as JSON to `[LLM_RESULTS_DIR]/`
4. Validate schema:
   ```bash
   python scripts/validate_schema.py --input [LLM_RESULTS_DIR]/
   ```

**Checkpoint**: Report how many samples were collected and how many were rejected (empty reason).

---

## Step 2: Feature Computation and Data Preparation

1. Verify schema consistency (no drift from previous iterations)
2. Join LLM labels with computed features
3. Validate class balance and missing rates:
   ```bash
   python scripts/prepare_dataset.py \
       --llm-results [LLM_RESULTS_DIR]/ \
       --output [DATASET_PATH]/training_data.csv
   python scripts/data_stats.py --dataset [DATASET_PATH]/training_data.csv
   ```

**Checkpoint**: Show class distribution. If severe imbalance (>5:1), flag and ask user whether to proceed or re-sample.

---

## Step 3: Train Lightweight ML Model

1. Train `[ML_FRAMEWORK]` model on prepared dataset
2. Track experiment with MLflow (or alternative if not available):
   ```bash
   python scripts/train_model.py \
       --dataset [DATASET_PATH]/training_data.csv \
       --model-output [MODEL_OUTPUT_PATH]/
   ```
3. Run quality gate:
   ```bash
   python scripts/quality_gate.py --model [MODEL_OUTPUT_PATH]/
   ```

**Checkpoint**: Report train/validation F1 and confirm model artifact was saved.

---

## Step 4: Accuracy Validation

1. Compare model accuracy against human-verified ground truth:
   ```bash
   python scripts/compare_accuracy.py --all-verified [VERIFIED_DIR]/
   ```
2. Log accuracy for this iteration:
   ```bash
   python scripts/save_accuracy_log.py \
       --ticket [TICKET_ID] \
       --ml-f1 <value> \
       --llm-f1 <value> \
       --api-cost <usd>
   ```

### Decision

| Result | Action |
|--------|--------|
| Accuracy ≥ `[TARGET]` | ✅ Loop complete — proceed to implementation |
| Accuracy < `[TARGET]` | Invoke `/llm-distil-verify` for root cause analysis, then return to Step 1 |
| Quality gate fails | Fix the failure before re-training — do not skip |

**Checkpoint**: State whether target was met. If not, invoke `/llm-distil-verify` before continuing.
