# ML Test Checklist

> **Purpose**: Quality gates for each iteration of the LLM → ML distillation loop.  
> Run all applicable checks before marking a training iteration complete.  
> Replace `[TARGET]` and `[LATENCY_TARGET]` / `[THROUGHPUT_TARGET]` with your project values.

---

## Data Quality Tests
_Run after LLM inference, before training._

- [ ] Schema validation: all LLM output rows match the schema in `ml-schema.md` Section 3
- [ ] No empty `reason` fields — samples with empty `reason` removed from training data
- [ ] All `prediction` values are within the defined class label set (Section 1)
- [ ] All `confidence` values are in `[0.0, 1.0]`
- [ ] Class balance: no class < 5% of dataset _(flag as warning; document if intentional)_
- [ ] Train / val / test splits created with no overlap
- [ ] No label leakage: target column is absent from feature columns

---

## Model Quality Tests
_Run after every training iteration._

- [ ] Validation F1 ≥ `[TARGET]` on held-out val set
- [ ] Precision / Recall per class reviewed — no class recall < 0.5 _(except documented minority class)_
- [ ] Feature importance output makes domain sense _(top features are explainable)_
- [ ] MLflow run logged: metrics, params, and model artifact all present

---

## Regression Tests
_Run before any model release or update._

- [ ] All human-verified samples still classified correctly after the model update
- [ ] `compare_accuracy.py --all-verified` passes with F1 ≥ `[TARGET]`
- [ ] No sample-specific special-casing in code _(grep for `if sample_id ==` patterns)_

---

## Integration Tests

- [ ] Prediction interface: valid input → expected output class _(smoke test)_
- [ ] Prediction interface: invalid / malformed input → clean error, not silent failure
- [ ] Full pipeline runs end-to-end: LLM inference → JSON parse → schema validation → training dataset → trained model
- [ ] Dataset preparation script: output columns match `ml-schema.md` Section 4

---

## Performance Tests
_Run before production deploy. Optional for PoC iterations._

- [ ] Inference latency ≤ `[LATENCY_TARGET]` ms on target hardware
- [ ] Batch inference throughput ≥ `[THROUGHPUT_TARGET]` samples/sec
- [ ] Model artifact size within deployment constraints

---

## Iteration Completion Gate

All of the following must be true before closing a distillation loop iteration:

| Gate | Check |
|------|-------|
| Data quality | All data quality tests pass |
| Model accuracy | Val F1 ≥ `[TARGET]` |
| Regression | All human-verified samples still correct |
| Logging | MLflow run and accuracy log both saved |
| Human review | At least 1 new human-verified sample confirms model output |
