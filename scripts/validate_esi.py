"""Validate synthetic ESI training data in JSONL format.

Checks every record for JSON validity, required keys, valid ESI label,
text quality, ID uniqueness, and duplicate text.  Optionally rewrites
the file with normalised JSON formatting (--fix).

Usage:
    python -m scripts.validate_esi data/esi_5_data.jsonl
    python -m scripts.validate_esi data/esi_5_data.jsonl --fix
    python -m scripts.validate_esi data/esi345_sample.jsonl --labels 3 4 5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED_KEYS = {"text", "label"}
ALL_ESI_LABELS = {1, 2, 3, 4, 5}
MIN_TEXT_LENGTH = 10


def _normalise(text: str) -> str:
    """Lower-case, collapse whitespace — used for near-duplicate detection."""
    return " ".join(text.lower().split())


def validate(
    path: Path,
    allowed_labels: set[int],
) -> tuple[list[dict], list[str], dict[int, int]]:
    """Return (records, issues) after validating every line in *path*."""
    records: list[dict] = []
    issues: list[str] = []
    seen_ids: dict[str, int] = {}
    seen_texts: dict[str, int] = {}
    label_counts: dict[int, int] = {}

    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, 1):
            raw = raw.strip()
            if not raw:
                continue

            try:
                record = json.loads(raw)
            except json.JSONDecodeError as exc:
                issues.append(f"line {lineno}: invalid JSON — {exc}")
                continue

            if not isinstance(record, dict):
                issues.append(f"line {lineno}: expected JSON object, got {type(record).__name__}")
                continue

            missing = REQUIRED_KEYS - record.keys()
            if missing:
                issues.append(f"line {lineno}: missing key(s) {missing}")
                continue

            label = record["label"]
            if not isinstance(label, int) or label not in allowed_labels:
                issues.append(
                    f"line {lineno}: label {label!r} not in allowed set {sorted(allowed_labels)}"
                )
            else:
                label_counts[label] = label_counts.get(label, 0) + 1

            text = record["text"]
            if not isinstance(text, str):
                issues.append(f"line {lineno}: 'text' is not a string ({type(text).__name__})")
                continue
            if text != text.strip():
                issues.append(f"line {lineno}: 'text' has leading/trailing whitespace")
            if len(text.strip()) < MIN_TEXT_LENGTH:
                issues.append(f"line {lineno}: 'text' too short ({len(text.strip())} chars, min {MIN_TEXT_LENGTH})")

            rec_id = record.get("id")
            if rec_id is not None:
                if rec_id in seen_ids:
                    issues.append(f"line {lineno}: duplicate id {rec_id!r} (first seen line {seen_ids[rec_id]})")
                else:
                    seen_ids[rec_id] = lineno

            norm = _normalise(text)
            if norm in seen_texts:
                issues.append(
                    f"line {lineno}: near-duplicate text of line {seen_texts[norm]}"
                )
            else:
                seen_texts[norm] = lineno

            records.append(record)

    return records, issues, label_counts


def fix(records: list[dict], path: Path) -> None:
    """Rewrite *path* with normalised JSON (sorted keys, separators with spaces)."""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
    print(f"\nRewrote {len(records)} records to {path} (normalised formatting)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate synthetic ESI JSONL training data")
    parser.add_argument(
        "path", type=Path,
        help="Path to the JSONL file to validate",
    )
    parser.add_argument(
        "--labels", type=int, nargs="+", default=None,
        help="Allowed ESI label values (default: 1-5). e.g. --labels 3 4 5",
    )
    parser.add_argument(
        "--fix", action="store_true",
        help="Rewrite file with normalised JSON formatting after validation",
    )
    args = parser.parse_args()

    allowed = set(args.labels) if args.labels else ALL_ESI_LABELS

    if not args.path.exists():
        print(f"ERROR: file not found — {args.path}")
        sys.exit(1)

    records, issues, label_counts = validate(args.path, allowed)

    total = len(records)
    n_issues = len(issues)
    print(f"File:     {args.path}")
    print(f"Records:  {total}")
    print(f"Labels:   {', '.join(f'ESI-{k}={v}' for k, v in sorted(label_counts.items()))}")
    print(f"Issues:   {n_issues}")

    if issues:
        print("\n--- Issues ---")
        for issue in issues:
            print(f"  {issue}")
    else:
        print("\nAll records passed validation.")

    if args.fix:
        if not records:
            print("\nNo valid records to write.")
        else:
            fix(records, args.path)

    sys.exit(1 if issues else 0)


if __name__ == "__main__":
    main()
