---
mode: agent
description: LLM → lightweight ML distillation loop — 4-step iterative process for knowledge distillation
---

# ML Distillation Loop: LLM → Lightweight ML

> **Purpose**: Use an LLM as a teacher to generate labeled training data (including reasoning), then distill that knowledge into a lightweight ML model suitable for low-latency, low-cost production inference.  
> **Reference**: Knowledge Distillation (Hinton et al., 2015); LLM-as-Teacher paradigm (2023+)

---

## Framework Selection

Choose your student model framework based on task type. Decide at project start and replace `[ML_FRAMEWORK]` throughout this guide.

| Task type | LLM Teacher | Student model candidates | Training API | Main metrics |
|-----------|-------------|--------------------------|--------------|--------------|
| **Tabular / Structured** | Text LLM (OpenAI / Google etc.) | **LightGBM** / XGBoost / sklearn | Custom train script | F1 / Accuracy / AUC |
| **NLP / Text** | Text LLM (OpenAI / Anthropic etc.) | DistilBERT / mBART / T5-small (HuggingFace) | `trainer.train()` | F1 / BLEU / ROUGE / EM |
| **Audio (raw waveform)** | Audio-capable LLM | Whisper fine-tune / wav2vec2 / EnCodec | `Seq2SeqTrainer` | WER / CER / F1 |
| **Image** | Multimodal LLM | EfficientNet / ViT / CLIP (torchvision / timm) | `Trainer / Lightning` | mAP / Top-k Acc / IoU |
| **Video** | Video-capable LLM | VideoMAE / TimeSformer / X-CLIP | `HF Trainer` | Action Acc / mAP |
| **Audio features → Tabular** | Audio-capable LLM | LightGBM (spectral features as input) | Custom train script | F1 / Accuracy |

> **LLM Teacher**: Always use the latest frontier model from your provider. Avoid pinning to a specific version. Model quality improves frequently.  
> **Audio vs Audio Features → Tabular**: Raw waveform / spectrogram input → "Audio". Extracted statistical features (MFCC, spectral centroid) as numeric vector → "Audio features → Tabular" (LightGBM).

---

## Loop Structure (4 Steps, Iterate Until Target Met)

```
Step 1: LLM inference — generate labeled data (with reasoning)
    ↓
Step 2: Feature computation and data preparation
    ↓
Step 3: Train lightweight ML model and evaluate
    ↓
Step 4: Accuracy validation → done if OK / loop back to Step 1 if not
```

---

## Step 1: LLM Inference — Generate Labeled Data

### Tasks

1. **Acquire input samples**: Extract features or prepare raw inputs from your dataset
2. **Run LLM inference**: Pass inputs to the LLM teacher; collect structured JSON output
   - **Required**: Include reasoning in output (`reason` field) — this is the chain-of-thought signal
3. **Store results**: Save output as JSON to `[LLM_RESULTS_DIR]/`

### LLM Prompt Design Requirements

- Encourage Chain-of-Thought: "Explain your reasoning step by step before giving the final decision"
- Output format: structured JSON matching your project's schema
- Include a `reason` field (English) explaining the inference decision
- Samples with empty `reason` are **rejected** from training data (quality rule)
- Example prompt structure:
  ```
  Given the following input data:
  [INPUT_FEATURES_JSON]
  
  Classify this into one of: [CLASS_LIST]
  
  Respond with JSON:
  {
    "prediction": "<class_name>",
    "confidence": <0.0-1.0>,
    "reason": "<step-by-step reasoning>"
  }
  ```

### Target Sample Counts

| Phase | Sample count | Purpose |
|-------|--------------|---------|
| PoC | ~50–100 | Schema validation, pipeline smoke test |
| Initial training | ~500–1000 | First evaluatable model |
| Production | ~5000+ | Generalization and edge case coverage |

> Adjust based on task complexity and class balance requirements.

---

## Step 2: Feature Computation and Data Preparation

### Schema Consistency Check (Required First)

Before joining data, verify that:
1. LLM output schema matches the expected format
2. Feature column names match the model's expected input features
3. No schema drift from previous iterations (e.g., added/removed feature columns)

```bash
# Validate LLM output schema (replace with your validation command)
python scripts/validate_schema.py --input [LLM_RESULTS_DIR]/

# Check feature completeness
python scripts/check_features.py --dataset [PREPARED_DATASET_PATH]
```

> **If schema change is needed**: Update schema documentation first, then re-generate affected data. Track schema versions.

### Data Preparation Tasks

1. Join LLM labels with computed features
2. Validate against schema (no null labels, no missing required features)
3. Check feature statistics (missing rate, distribution, class balance)

```bash
python scripts/prepare_dataset.py \
    --llm-results [LLM_RESULTS_DIR]/ \
    --output [DATASET_PATH]/training_data.csv

# Inspect class distribution
python scripts/data_stats.py --dataset [DATASET_PATH]/training_data.csv
```

---

## Step 3: Train Lightweight ML Model

### Model Training

```bash
# Replace with your training command
python scripts/train_model.py \
    --dataset [DATASET_PATH]/training_data.csv \
    --model-output [MODEL_OUTPUT_PATH]/ \
    --framework [ML_FRAMEWORK]
```

> Accuracy target: define a target F1 / accuracy score and compare against it in Step 4.

### Experiment Tracking (MLflow autolog — zero boilerplate)

```python
import mlflow
import mlflow.lightgbm  # or mlflow.sklearn, mlflow.transformers, etc.

mlflow.set_experiment("[EXPERIMENT_NAME]")
with mlflow.start_run():
    mlflow.lightgbm.autolog()  # automatically logs: metrics, params, feature importance, model artifact
    # ... your existing training code ...
    model.fit(X_train, y_train)
```

```bash
# View past experiments in browser
mlflow ui  # opens http://localhost:5000
```

> MLflow writes to local `mlruns/` only (no server needed). Install: `pip install mlflow`.

---

## Step 4: Accuracy Validation

### Automated Validation

```bash
# Run quality gate (tests + accuracy checks)
python scripts/quality_gate.py --model [MODEL_OUTPUT_PATH]/
```

### ML vs LLM Comparison

```bash
# Compare all verified samples
python scripts/compare_accuracy.py \
    --all-verified [VERIFIED_SAMPLES_DIR]/ \
    --predicted [MODEL_PREDICTIONS_DIR]/

# Single sample comparison
python scripts/compare_accuracy.py \
    --verified [VERIFIED_SAMPLES_DIR]/sample.json \
    --predicted output.json
```

### Log Accuracy Results (Required on Completion)

Record both ML and LLM scores to track distillation progress over iterations:

```bash
python scripts/save_accuracy_log.py \
    --ticket [TICKET_ID] \
    --model-version [MODEL_NAME]_v[N] \
    --ml-f1 [f1_score] \
    --llm-f1 [llm_f1_score] \
    --api-cost [cost_usd] \
    --notes "First distillation. Unresolved misclassifications: [note]"

# View trend
python scripts/save_accuracy_log.py --trend
```

### Loop Continuation Decision

| Result | Action |
|--------|--------|
| F1 > target AND human review OK | ✅ Complete — save accuracy log, close ticket |
| F1 < target (insufficient data) | 🔄 Return to Step 1 — collect more labeled data |
| F1 < target (high-uncertainty samples clustered) | 🔄 **Uncertainty Sampling** → return to Step 1 (see below) |
| Human review fails | 🔍 Run `ml-accuracy-verify.prompt.md` for root cause analysis |
| Root cause C (model problem) confirmed by verify loop | 🔄 Return to Step 1 — more LLM data generation required |

### Uncertainty Sampling (Active Learning)

When accuracy falls short, prioritize re-labeling the samples where the model is most uncertain. This maximizes accuracy improvement per LLM API call.

```python
import numpy as np
import pandas as pd

# Get prediction probabilities from trained model
proba = model.predict_proba(X)  # shape: (n_samples, n_classes)

# Compute prediction entropy (higher = more uncertain)
entropy = -np.sum(proba * np.log(proba + 1e-9), axis=1)

# Rank samples by uncertainty
high_uncertainty = pd.DataFrame({
    "sample_id": sample_ids,
    "entropy": entropy
}).sort_values("entropy", ascending=False).head(20)

print("High-uncertainty samples to re-label with LLM:")
print(high_uncertainty)
```

> Pass these 20 samples to the LLM in the next Step 1 iteration.  
> Reference: Uncertainty Sampling — Active Learning (Lewis & Gale, 1994; Settles, 2009)
