# ML Data Schema

> **Purpose**: Define data contracts for the LLM → ML distillation pipeline.  
> Fill this out during the design phase. Keep it synchronized with training scripts and model code.  
> Update when feature columns change, class labels are added/removed, or the model interface changes.

---

## 1. Task Type

| Field | Value |
|-------|-------|
| Task type | _(Tabular / NLP / Audio / Image / Video / Audio Features→Tabular)_ |
| Student model | _(e.g., LightGBM, DistilBERT, Whisper fine-tune)_ |
| LLM Teacher | _(text LLM / audio-capable LLM — always use latest frontier model)_ |
| Target metric | _(e.g., F1 ≥ 0.80, WER ≤ 15%, mAP ≥ 0.75)_ |
| Class labels | _(list all valid output classes, one per line)_ |

---

## 2. Input Feature Schema

> **Tabular / Audio Features→Tabular**: define columns in the table below.  
> **NLP / Audio / Image / Video**: describe the raw input format in the "Raw Input Format" section instead.

### Tabular / Structured Features

| Column name | Type | Value range / format | Description |
|-------------|------|---------------------|-------------|
| `feature_1` | float | 0.0–1.0 | _(description)_ |
| `feature_2` | int | 0–N | _(description)_ |
| ... | | | |

_Add or remove rows as needed. Do not include the target label here — it lives in Section 4._

### Raw Input Format (NLP / Audio / Image / Video)

| Field | Spec |
|-------|------|
| Input type | _(text string / audio file / image / video)_ |
| Format | _(wav 16kHz mono / RGB 224×224 / mp4 30fps / UTF-8 text)_ |
| Preprocessing | _(tokenization / STFT / resize+normalize / frame sampling)_ |
| Max size / length | _(max token length / max duration / max resolution)_ |

---

## 3. LLM Output Schema (Teacher)

This JSON structure is **universal** across all task types.

```json
{
  "prediction": "<class_name>",
  "confidence": 0.85,
  "reason": "<step-by-step reasoning — REQUIRED, never empty>"
}
```

**Validation rules:**
- `prediction` must be one of the class labels listed in Section 1
- `confidence` must be in `[0.0, 1.0]`
- `reason` must be non-empty — samples with empty `reason` are **rejected** from training data (quality rule)

> If your task requires additional fields (e.g., per-class scores, structured sub-predictions), extend this schema and document the extensions here.

---

## 4. Training Dataset Schema

The joined dataset (LLM output + computed features) used for student model training.

| Column | Source | Type | Notes |
|--------|--------|------|-------|
| `sample_id` | generated | str | Unique identifier |
| _(feature columns from Section 2)_ | computed | — | One row per column |
| `label` | LLM output | str | `prediction` field |
| `confidence` | LLM output | float | Optional: use as sample weight during training |
| `reason` | LLM output | str | Quality check only — not used as a training feature |
| `split` | assigned | str | `train` / `val` / `test` — no overlap allowed |

---

## 5. Model Prediction Interface

Define the input/output contract for the trained student model.

### Input

```python
# Tabular / Audio Features→Tabular
features: dict[str, float | int | str]  # column name → value

# NLP
text: str

# Audio
audio_path: str  # path to .wav or .mp3 file

# Image / Video
file_path: str   # path to image or video file
```

### Output

```python
{
    "prediction": str,    # class label (one of the labels in Section 1)
    "confidence": float   # model probability for the top predicted class
}
```

---

## 6. Schema Version History

Update this table whenever the schema changes. Breaking changes require re-generating affected LLM inference data.

| Version | Date | Change summary | Re-generation required |
|---------|------|---------------|------------------------|
| v1 | YYYY-MM-DD | Initial schema | — |
