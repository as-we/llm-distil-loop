"""
llm-distil-loop — Quick Demo
==============================
Demonstrates the 4-step LLM → ML distillation loop using:
  - A toy dataset (Iris, no download needed — included in scikit-learn)
  - A mock LLM teacher (no API key required)
  - LightGBM as the student model

Steps:
  1. Mock LLM generates labels + chain-of-thought reasoning
  2. Feature preparation and quality gate (reject empty reasons)
  3. Train LightGBM on distilled labels
  4. Validate accuracy against ground truth

Requirements:
  pip install scikit-learn lightgbm pandas
"""

import json
import random
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score
import lightgbm as lgb

random.seed(42)

# ── Config ─────────────────────────────────────────────────────────────────
LLM_RESULTS_DIR = []   # in-memory for demo; replace with file path in production
ACCURACY_TARGET = 0.85
IRIS_CLASSES    = ["setosa", "versicolor", "virginica"]

# ── Step 1: Mock LLM Teacher ────────────────────────────────────────────────
def mock_llm_teacher(features: dict) -> dict:
    """
    Simulates a frontier LLM classifying an Iris sample.

    In production, replace this with your actual LLM API call.
    The key contract: output must include a non-empty 'reason' field.

    Injects ~10% label noise and ~5% empty-reason samples to demonstrate
    the quality gate in Step 2.
    """
    sl, sw, pl, pw = (
        features["sepal_length"],
        features["sepal_width"],
        features["petal_length"],
        features["petal_width"],
    )

    # Rule-based heuristic (mimics what a real LLM would reason)
    if pl < 2.5:
        label, reason = "setosa", (
            f"Petal length {pl:.1f}cm is very short (< 2.5cm). "
            "Setosa is the only species with petals this small."
        )
    elif pl < 4.9 and pw < 1.7:
        label, reason = "versicolor", (
            f"Petal length {pl:.1f}cm and width {pw:.1f}cm fall in the "
            "intermediate range typical of versicolor."
        )
    else:
        label, reason = "virginica", (
            f"Large petal dimensions (length {pl:.1f}cm, width {pw:.1f}cm) "
            "strongly indicate virginica."
        )

    # Inject label noise (~10%)
    if random.random() < 0.10:
        label = random.choice([c for c in IRIS_CLASSES if c != label])
        reason = f"[NOISY] {reason}"

    # Inject empty reason (~5%) — these will be rejected by the quality gate
    if random.random() < 0.05:
        reason = ""

    return {"prediction": label, "confidence": round(random.uniform(0.7, 0.99), 2), "reason": reason}


print("=" * 60)
print("llm-distil-loop — Quick Demo")
print("=" * 60)

# ── Load toy dataset ─────────────────────────────────────────────────────────
iris = load_iris()
df = pd.DataFrame(iris.data, columns=["sepal_length", "sepal_width", "petal_length", "petal_width"])
df["true_label"] = [IRIS_CLASSES[i] for i in iris.target]

# ── Step 1: LLM Inference ────────────────────────────────────────────────────
print("\n[Step 1] Running mock LLM teacher on 150 samples...")
llm_results = []
for _, row in df.iterrows():
    result = mock_llm_teacher(row.to_dict())
    result.update({
        "sepal_length": row["sepal_length"],
        "sepal_width":  row["sepal_width"],
        "petal_length": row["petal_length"],
        "petal_width":  row["petal_width"],
    })
    llm_results.append(result)

print(f"  → {len(llm_results)} samples generated")

# ── Step 2: Quality Gate — reject empty reasons ───────────────────────────────
print("\n[Step 2] Applying quality gate (reject empty 'reason')...")
before = len(llm_results)
llm_results = [r for r in llm_results if r["reason"].strip()]
rejected = before - len(llm_results)
print(f"  → Rejected {rejected} samples (empty reason)")
print(f"  → {len(llm_results)} samples passed quality gate")

# Build training DataFrame
train_df = pd.DataFrame(llm_results)
FEATURES = ["sepal_length", "sepal_width", "petal_length", "petal_width"]
label_map = {c: i for i, c in enumerate(IRIS_CLASSES)}
train_df["label_id"] = train_df["prediction"].map(label_map)

X = train_df[FEATURES]
y = train_df["label_id"]
X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

print(f"\n  Class distribution (LLM labels):")
for cls, cnt in train_df["prediction"].value_counts().items():
    print(f"    {cls}: {cnt}")

# ── Step 3: Train LightGBM ────────────────────────────────────────────────────
print("\n[Step 3] Training LightGBM student model...")
model = lgb.LGBMClassifier(n_estimators=100, num_leaves=15, random_state=42, verbose=-1)
model.fit(X_train, y_train)

val_preds = model.predict(X_val)
val_f1 = f1_score(y_val, val_preds, average="macro")
print(f"  → Validation F1 (vs LLM labels): {val_f1:.3f}")

# ── Step 4: Validate against ground truth ────────────────────────────────────
print("\n[Step 4] Validating against ground truth (human labels)...")
true_labels = df.loc[train_df.index, "true_label"].map(label_map)
_, X_gt_val, _, y_gt_val = train_test_split(X, true_labels, test_size=0.2, random_state=42)

gt_preds = model.predict(X_gt_val)
gt_f1 = f1_score(y_gt_val, gt_preds, average="macro")
print(f"  → F1 vs ground truth: {gt_f1:.3f}  (target: {ACCURACY_TARGET})")

print("\n" + "=" * 60)
if gt_f1 >= ACCURACY_TARGET:
    print(f"✅ Target met ({gt_f1:.3f} >= {ACCURACY_TARGET})")
    print("   Loop complete — model ready for production.")
else:
    print(f"⚠️  Target not met ({gt_f1:.3f} < {ACCURACY_TARGET})")
    print("   → Run accuracy verification loop to diagnose:")
    print("     1. Collect human-verified samples")
    print("     2. Compare LLM vs ML vs human labels")
    print("     3. Identify root cause (noisy labels / missing features / insufficient data)")
    print("     4. Apply generic fix and re-run from Step 1")
print("=" * 60)

# ── Summary ───────────────────────────────────────────────────────────────────
print("\nAccuracy log (append to your project's accuracy log):")
print(json.dumps({
    "dataset":    "iris (toy demo)",
    "samples":    len(llm_results),
    "rejected":   rejected,
    "val_f1_llm": round(val_f1, 3),
    "val_f1_gt":  round(gt_f1, 3),
    "target":     ACCURACY_TARGET,
    "passed":     gt_f1 >= ACCURACY_TARGET,
}, indent=2))
