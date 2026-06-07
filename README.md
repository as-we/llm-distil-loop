# llm-distil-loop

**LLM → Lightweight ML Distillation Loop** — A structured workflow for using a frontier LLM as a teacher to generate labeled training data, then distilling that knowledge into a cost-efficient lightweight ML model for production use.

---

## Quick Demo

No API key required. Uses a mock LLM teacher and the Iris dataset.

```bash
pip install scikit-learn lightgbm pandas
python example/run.py
```

```
[Step 1] Running mock LLM teacher on 150 samples...
  → 150 samples generated

[Step 2] Applying quality gate (reject empty 'reason')...
  → Rejected 5 samples (empty reason)
  → 145 samples passed quality gate

[Step 3] Training LightGBM student model...
  → Validation F1 (vs LLM labels): 0.898

[Step 4] Validating against ground truth (human labels)...
  → F1 vs ground truth: 0.967  (target: 0.85)

✅ Target met (0.967 >= 0.85) — Loop complete.
```

The mock LLM injects ~10% label noise and ~5% empty-reason samples to demonstrate the quality gate.  
Replace `mock_llm_teacher()` in `example/run.py` with your real LLM API call.

---

## What This Is

A 4-step iterative loop:

```
Step 1: Generate labeled data using an LLM (teacher)
    ↓
Step 2: Compute features and join with labels
    ↓
Step 3: Train a lightweight ML model (student)
    ↓
Step 4: Validate accuracy → done if good / loop back if not
```

Combined with a companion accuracy-verification loop for root cause analysis when accuracy falls short.

---

## Why Use This

| Concern | LLM API (production) | Lightweight ML (distilled) |
|---------|---------------------|---------------------------|
| Latency | 1–5 seconds / call | <10ms |
| Cost | $0.01–0.10 / call | Near-zero (model runs locally) |
| Offline / batch | ❌ Requires internet | ✅ Fully local |
| Interpretability | Low | High (feature importance, SHAP) |
| Data requirements | None (zero-shot) | Requires labeled training data |

**Trade-off**: You invest LLM API cost upfront during data generation to eliminate that cost in production.

---

## Contents

```
llm-distil-loop/
├── README.md                                          ← This file
├── setup-checklist.md                                 ← Step-by-step integration guide
├── templates/
│   ├── ml-schema.md                                   ← Data contract template
│   │                                                     (input features, LLM output schema,
│   │                                                      training dataset, model interface)
│   │                                                     Kiro: copy to .kiro/settings/templates/
│   │                                                     Standalone: copy to docs/ or project root
│   └── ml-test-checklist.md                           ← Iteration quality gate checklist
│                                                         Kiro: copy to .kiro/settings/templates/
│                                                         Standalone: copy to docs/ or project root
│                                                         Note: NOT .kiro/settings/templates/specs/
│                                                         These files are pipeline-wide, not spec-scoped.
├── github/
│   └── prompts/
│       ├── kiro-ml-distill-loop.prompt.md             ← 4-step distillation loop
│       │                                                 copy to: .github/prompts/
│       └── kiro-ml-accuracy-verify.prompt.md          ← 5-step accuracy verification loop
│                                                         copy to: .github/prompts/
└── kiro/
    └── settings/
        └── rules/
            └── ml-distillation-rules.md               ← Non-negotiable loop rules (Kiro auto-loads)
                                                          copy to: .kiro/settings/rules/
                                                          Standalone: reference in contribution guide
```

See `setup-checklist.md` for step-by-step integration instructions.

---

## Framework Selection

Choose your student model framework based on your task type:

| Task type | LLM Teacher | Student model candidates | Main metrics |
|-----------|-------------|--------------------------|--------------|
| **Tabular / Structured** | Text LLM (OpenAI / Google etc.) | **LightGBM** / XGBoost / sklearn | F1 / Accuracy / AUC |
| **NLP / Text** | Text LLM (OpenAI / Anthropic etc.) | DistilBERT / mBART / T5-small | F1 / BLEU / ROUGE / EM |
| **Audio (raw waveform)** | Audio-capable LLM (Google / OpenAI etc.) | Whisper fine-tune / wav2vec2 | WER / CER / F1 |
| **Image** | Multimodal LLM (OpenAI / Google etc.) | EfficientNet / ViT / CLIP | mAP / Top-k Acc / IoU |
| **Video** | Video-capable LLM (Google / OpenAI etc.) | VideoMAE / TimeSformer / X-CLIP | Action Acc / mAP |
| **Audio features → Tabular** | Audio-capable LLM (Google / OpenAI etc.) | LightGBM (spectral features as input) | F1 / Accuracy |

> **Audio vs Audio Features → Tabular**: If you pass raw waveforms or spectrograms directly → use "Audio". If you first extract statistical features (MFCC, spectral centroid, energy) and feed a numeric vector → use "Audio features → Tabular" (LightGBM).

> **LLM Teacher**: Always use the latest frontier model from your provider. Avoid pinning to a specific version — model quality improves frequently.

---

## Setup

### Option A: With Kiro SDD

Copy the prompts to your project's `.github/prompts/` directory:

```bash
cp prompts/ml-distill-loop.prompt.md     /your-project/.github/prompts/kiro-ml-distill-loop.prompt.md
cp prompts/ml-accuracy-verify.prompt.md  /your-project/.github/prompts/kiro-ml-accuracy-verify.prompt.md
```

Then customize the `[PLACEHOLDER]` values in each file to match your project structure.

Invoke in your Kiro workflow:
- `/kiro-ml-distill-loop` — run the 4-step distillation loop
- `/kiro-ml-accuracy-verify` — run accuracy verification and root cause analysis

### Option B: Standalone (no Kiro SDD)

Use `ml-distill-loop.prompt.md` and `ml-accuracy-verify.prompt.md` directly as AI agent prompts in any IDE with AI support (VS Code Copilot, Cursor, Windsurf, etc.).

---

## Key Concepts

### Knowledge Distillation
The theoretical basis. Originally published as [Distilling the Knowledge in a Neural Network](https://arxiv.org/abs/1503.02531) (Hinton et al., 2015). This workflow adapts the concept to the LLM-as-teacher paradigm (2023+), where the teacher model generates labeled datasets rather than soft probabilities.

### Uncertainty Sampling (Active Learning)
When accuracy falls short of target, prioritize re-labeling samples where the model is most uncertain (highest entropy). This maximizes accuracy improvement per LLM API call.  
Reference: [Active Learning Literature Survey](https://burrsettles.com/pub/settles.activelearning.pdf) (Settles, 2009).

### MLflow Experiment Tracking
The loop uses MLflow autolog for zero-boilerplate tracking of metrics, parameters, and model artifacts. All data is stored locally in `mlruns/`. No server required.

---

## The "So What" Principle

After finding a concept name during investigation, always answer: **"How does this change my design?"**  
Concept-name collection must not become the goal. The distillation loop produces value when it eliminates production LLM dependency — not when it demonstrates technical sophistication.

---

## License

Apache License 2.0 — use freely in commercial and open-source projects.

Consistent with LightGBM, scikit-learn, and MLflow. Includes patent protection clause.
