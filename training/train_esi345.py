"""Train a TF-IDF + Logistic Regression classifier for ESI 3/4/5.

Usage:
    python -m training.train_esi345
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

VALID_LABELS = {3, 4, 5}
DATA_PATH = Path("data/esi345_sample.jsonl")
ARTIFACT_DIR = Path("artifacts")


def load_dataset(path: Path) -> tuple[list[str], list[int]]:
    texts: list[str] = []
    labels: list[int] = []
    with open(path, encoding="utf-8") as f:
        for lineno, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            label = record["label"]
            if label not in VALID_LABELS:
                print(f"WARNING: skipping line {lineno} with invalid label {label}")
                continue
            texts.append(record["text"])
            labels.append(label)
    return texts, labels


def main() -> None:
    if not DATA_PATH.exists():
        print(f"ERROR: dataset not found at {DATA_PATH}")
        sys.exit(1)

    texts, labels = load_dataset(DATA_PATH)
    print(f"Loaded {len(texts)} examples  (3={labels.count(3)}, 4={labels.count(4)}, 5={labels.count(5)})")

    X_train, X_test, y_train, y_test = train_test_split(
        texts, labels, test_size=0.20, random_state=42, stratify=labels,
    )
    print(f"Train: {len(X_train)}  Test: {len(X_test)}")

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=5000)
    X_train_tfidf = vectorizer.fit_transform(X_train)
    X_test_tfidf = vectorizer.transform(X_test)

    model = LogisticRegression(
        max_iter=1000, class_weight="balanced", random_state=42,
    )
    model.fit(X_train_tfidf, y_train)

    y_pred = model.predict(X_test_tfidf)
    print(f"\nAccuracy: {accuracy_score(y_test, y_pred):.2%}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred, labels=[3, 4, 5]))

    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
    vectorizer_path = ARTIFACT_DIR / "vectorizer.joblib"
    model_path = ARTIFACT_DIR / "model.joblib"
    joblib.dump(vectorizer, vectorizer_path)
    joblib.dump(model, model_path)
    print(f"Saved vectorizer -> {vectorizer_path}")
    print(f"Saved model      -> {model_path}")


if __name__ == "__main__":
    main()
