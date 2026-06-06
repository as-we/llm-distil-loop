---
description: "Run 5-step accuracy verification: compare ML output against human labels → root cause analysis → apply generic fix → re-verify"
---

# ML Accuracy Verification Loop

> Invoke when distillation loop accuracy falls short of target, or proactively when accuracy improvement is needed.
>
> **Rules enforced**:
> - Ground truth is the human label — never the LLM output
> - Generic fixes only — sample-specific patches are absolutely forbidden
> - Re-verify across ALL samples after every fix (not just the failing ones)

## User Input

```text
$ARGUMENTS
```

## Pre-Execution: Read Project Schema

Check for schema file at `.specify/templates/ml-schema.md`, `.kiro/settings/templates/ml-schema.md`, or `docs/ml-schema.md`.  
Use the defined `[VERIFIED_DIR]` and `[TARGET]` values, or ask the user.

---

## Step 1: Collect Human-Labeled Ground Truth

Check for existing verified samples first — reuse before collecting new:

```bash
python scripts/verify.py --list
```

If verified samples exist → skip to **Step 2**.  
If not, collect:
```bash
python scripts/verify.py add \
    --sample-id [SAMPLE_ID] \
    --correct-label [LABEL] \
    --notes "[human observations]"
```

**Checkpoint**: Confirm at least 1 human-verified sample exists before proceeding.

---

## Step 2: Three-Way Comparison (LLM vs ML vs Human)

```bash
python scripts/compare_accuracy.py --all-verified [VERIFIED_DIR]/
```

Display a table: sample ID | human label | LLM output | ML output | ML correct?

**Checkpoint**: Identify which samples ML got wrong and which LLM got right/wrong.

---

## Step 3: Root Cause Classification

Classify each error into one of four categories:

| Category | Description | Fix direction |
|----------|-------------|--------------|
| **A — Feature missing** | The discriminating signal is not in the feature set | Add features in Step 2 of distillation loop |
| **B — Label noise** | LLM generated incorrect labels for these cases | Re-generate LLM labels with improved prompt |
| **C — Insufficient data** | Model has not seen enough examples of this pattern | Collect more samples in Step 1 of distillation loop |
| **D — Algorithm mismatch** | Task requires a different model architecture | Change `[ML_FRAMEWORK]` or model type |

For each failing sample, state the category and evidence.

**Checkpoint**: Present root cause summary (e.g., "70% Category B, 30% Category A"). Ask user to confirm before applying fixes.

---

## Step 4: Apply Generic Fix

Based on root cause:

- **Category A**: Update feature extraction pipeline. Document new features in `ml-schema.md`.
- **Category B**: Improve LLM prompt (add examples, clarify edge cases). Re-run Step 1 of distillation loop.
- **Category C**: Expand dataset. Re-run Step 1 of distillation loop with targeted sampling.
- **Category D**: Change model type. Document decision in project ADR or `ml-schema.md`.

**Absolute prohibition**: Do NOT write code that special-cases specific sample IDs.

**Checkpoint**: Confirm fix type and show the change made.

---

## Step 5: Re-Verify Across ALL Samples

```bash
python scripts/compare_accuracy.py --all-verified [VERIFIED_DIR]/
python scripts/save_accuracy_log.py \
    --ticket [TICKET_ID] \
    --ml-f1 <new_value> \
    --llm-f1 <llm_value> \
    --api-cost <usd>
```

### Decision

| Result | Action |
|--------|--------|
| Accuracy ≥ `[TARGET]` | ✅ Verification complete — return to distillation loop Step 4 |
| Accuracy < `[TARGET]` | Return to **Step 2** with updated samples |
| Root cause unresolved | Escalate to user — do not loop indefinitely without human input |
