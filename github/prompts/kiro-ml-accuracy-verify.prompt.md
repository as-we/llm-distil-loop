---
mode: agent
description: ML accuracy verification loop — root cause analysis and generic fixes when accuracy falls short
---

# ML Accuracy Verification Loop

> **Purpose**: When ML (or LLM) accuracy fails a target, identify the root cause using human-labeled ground truth, apply only generic fixes, and re-verify across all samples.  
> **When to invoke**: From `ml-distill-loop.prompt.md` Step 4 when human review fails, or proactively when accuracy improvement is needed.

---

## Loop Structure (5 Steps, Iterate Until Target Met)

```
Step 1: Collect human-labeled ground truth
    ↓
Step 2: Three-way comparison: LLM vs ML vs baseline
    ↓
Step 3: Identify root cause (A / B / C / D classification)
    ↓
Step 4: Apply generic fix (no sample-specific patches)
    ↓
Step 5: Re-verify across ALL samples → done if OK / return to Step 2 if not
```

---

## Step 1: Collect Human-Labeled Ground Truth

### Check existing verified samples first (reuse before collecting new)

```bash
# List registered verified samples
python scripts/verify.py --list
```

> If verified samples already exist → skip collection and go directly to **Step 2**.  
> Human-verified data is cumulative — each sample verified this session is used automatically in future accuracy checks (no repeated LLM cost).

### Collect new samples (only when necessary)

1. Inspect the target sample using your domain-appropriate review tool
2. Determine the correct label using domain expertise
3. Record tolerance: accuracy ± [human tolerance, e.g., 5%]
4. Register:

```bash
python scripts/verify.py add \
    --sample-id [SAMPLE_ID] \
    --correct-label [LABEL] \
    --notes "[human observations]"
```

---

## Step 2: Three-Way Comparison

### Automated comparison

```bash
# All verified samples at once (recommended)
python scripts/compare_accuracy.py --all-verified [VERIFIED_DIR]/

# Single sample
python scripts/compare_accuracy.py \
    --verified [VERIFIED_DIR]/[sample].json \
    --predicted [output.json]
```

> **Important**: After any fix, always run `--all-verified` — not just the failing sample.  
> Fixing one sample while breaking another is a failure.

### Comparison table template

| Sample | Human label | LLM prediction | ML prediction | Baseline | Notes |
|--------|-------------|----------------|---------------|----------|-------|
| sample_001 | class_A | ✅ class_A | ❌ class_B | ✅ class_A | ML misclassification |
| sample_002 | class_B | ❌ class_A | ❌ class_A | ❌ class_A | All models wrong |

Fill this table before root cause analysis. Patterns this table reveals:
- If only ML is wrong → likely root cause C (model problem)
- If LLM and ML are both wrong → likely root cause A (feature/data problem) or B (algorithmic bug)
- If all three are wrong → root cause A (features don't capture the signal)

---

## Step 3: Root Cause Identification

### Root cause categories

| Category | Symptom | How to confirm |
|----------|---------|----------------|
| **A. Data problem** | Features don't reflect the actual signal | Plot feature distributions; look for missing or inverted signals |
| **B. Algorithmic bug** | Baseline calculation has a structural error | Write a unit test that reproduces the incorrect output |
| **C. Model problem** | Training data is biased, too small, or unbalanced | Inspect training data distribution; check class counts |
| **D. Threshold / tuning problem** | Parameter tuned to one sample, breaks others | Test the same parameter on 3+ different samples |

### LLM-assisted root cause analysis prompt

```
Analyze the prediction error for this sample.

Human label: [CORRECT_LABEL]
Model output: [PREDICTED_LABEL] (score: [SCORE])
Feature data: [FEATURE_JSON]
LLM prediction: [LLM_OUTPUT]
LLM reasoning: [LLM_REASON]

Classify the root cause into one of the categories below,
identify the most likely cause, and suggest a GENERIC fix
(no sample-specific workarounds):

A. Data problem — features don't reflect reality
B. Algorithmic bug — structural error in baseline computation
C. Model problem — training data insufficient or biased
D. Threshold/tuning problem — parameter over-fitted to this sample
```

---

## Step 4: Apply Generic Fixes

### Fix acceptance criteria

| Fix type | Accept? |
|----------|---------|
| Fix structural bug that reproduces across all data | ✅ Accept |
| Improve algorithm preconditions or invariants | ✅ Accept |
| Parameter tuned specifically to one sample's pattern | ❌ Reject |
| `if sample_id == "xxx": ...` or equivalent special-casing | ❌ Never — absolute rejection |

### Fix procedure

1. **Write a reproduction test first** (confirm the bug is reproducible)
2. Implement the fix
3. **Verify on ALL human-labeled samples** — confirm no regression
4. Run full quality gate

```bash
# Run full test suite
pytest tests/ -v

# Run on all verified samples
python scripts/compare_accuracy.py --all-verified [VERIFIED_DIR]/

# Full quality gate
python scripts/quality_gate.py
```

---

## Step 5: Re-Verify

### Checklist

```bash
# 1. All tests pass
pytest tests/ -v

# 2. All verified samples — check no regression
python scripts/compare_accuracy.py --all-verified [VERIFIED_DIR]/
```

### Continuation decision

| Result | Action |
|--------|--------|
| All samples F1 > [TARGET] AND human review OK | ✅ Complete — return to `ml-distill-loop.prompt.md` and mark done |
| Root cause was **C (model problem / insufficient data)** | 🔄 **Return to `ml-distill-loop.prompt.md` Step 1** — more labeled data needed |
| Root cause **A/B/D** fixed but still below target | 🔄 Return to Step 2 — compare again |
| Fix improved one sample but degraded another | 🔄 Return to Step 2 — the fix introduced domain-specific bias |
| F1 improving but still below target (algorithm improved) | 🔄 **Return to `ml-distill-loop.prompt.md` Step 1** — data volume is the bottleneck |

> **Root cause C must always return to the distillation loop Step 1.**  
> Iterating within the accuracy-verify loop cannot fix a training data shortage.

---

## Core Principles

1. **Never special-case**: Any fix that makes sample X correct while not generalizing to the full dataset is rejected.
2. **Always test all verified samples**: A fix is only valid if it improves or maintains accuracy across all of them.
3. **Human review is not optional**: The ground truth label comes from a human; the verification loop exists to close the gap to that standard.
4. **Root cause C → exit this loop**: Only training data helps model problems. Don't spend more cycles here.
