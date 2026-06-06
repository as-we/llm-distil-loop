# ML Distillation Rules

> **Purpose**: Declare the non-negotiable rules that govern every iteration of the LLM → ML distillation loop.  
> When using with Kiro / cc-sdd, place this file at `.kiro/settings/rules/` so Kiro auto-loads it as a project rule.  
> When using standalone, reference this file in your team's contribution guide.

---

## Core Rules

### 1. No empty reasoning — data quality gate

LLM inference output **must** include a `reason` field (step-by-step reasoning).  
Any sample with an empty or missing `reason` is **rejected from training data** unconditionally.

> Rationale: The distillation value comes from the reasoning process, not just the label. Labels without reasoning are indistinguishable from naive annotation.

### 2. No sample-specific special-casing — generalization gate

Any code change of the form:
```python
if sample_id == "xxx":   # ❌ absolutely forbidden
    return special_value
```
is an absolute rejection. Document the policy in code review.

**Acceptable fixes**: structural bugs that reproduce across all data, algorithm precondition improvements.  
**Unacceptable fixes**: parameter tuning or logic that targets a specific sample's pattern.

### 3. Human review is not optional — accuracy gate

At least one human-verified sample must confirm model output before any training iteration is closed.  
The ground truth is the human label, not the LLM output.

> Rationale: LLMs can be systematically wrong in domain-specific ways. Human calibration catches distribution drift.

### 4. Accuracy must be logged every iteration — traceability gate

After every training run, record:
- ML model F1 (or task-appropriate metric)
- LLM teacher F1 (on the same verified sample set)
- LLM API cost for this iteration (USD)
- Model version identifier
- Notes on unresolved misclassifications

No training run is considered complete without this log entry.

### 5. All verified samples must pass regression — regression gate

After any model fix or update, run evaluation on **all** human-verified samples, not just the failing one.  
A fix that improves one sample while degrading another is **not a fix** — it is a regression.

### 6. Schema changes follow the version bump procedure — schema gate

When the training dataset schema changes (columns added/removed, class labels changed):
1. Update `templates/ml-schema.md` Section 6 (Version History) **before** changing any code
2. Identify which pipeline stages need re-execution (LLM inference / feature computation / training)
3. Document affected stages in the ML accuracy log for that iteration

> Breaking schema changes require full LLM re-inference for affected samples.

---

## Escalation: When to exit the accuracy-verify loop

When `ml-accuracy-verify` identifies root cause **C (model problem / insufficient data)**:

- Do **not** continue iterating within the accuracy-verify loop
- Return to `ml-distill-loop` Step 1 to collect more LLM-labeled training data
- Accuracy problems caused by data shortage cannot be resolved through algorithm fixes alone

---

## Quick Reference

| Rule | Gate | Violation consequence |
|------|------|-----------------------|
| Non-empty `reason` | Data quality | Sample rejected from training |
| No sample-specific code | Code review | PR blocked |
| Human review required | Accuracy | Iteration not closeable |
| Accuracy log mandatory | Traceability | Iteration not closeable |
| All-sample regression check | Regression | Fix considered invalid |
| Schema version bump first | Schema | Code change blocked |
