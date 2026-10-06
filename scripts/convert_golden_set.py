"""
Converts the hand-labeled eval/labeling_template.csv into the final
golden evaluation set deliverable: eval/golden_set.jsonl

Each line is one JSON object:
{
  "conversation_id": ...,
  "thread_text": "... full raw thread ...",
  "intent": "...",
  "severity": "...",
  "handling_strategy": "...",
  "privacy_requirement": "...",
  "automation_eligibility": "...",
  "reason": "...",
  "reference_reply_notes": "...",
  "labeler_notes": "..."
}

Only rows where at minimum intent/severity/handling_strategy are filled in
are included -- unlabeled or partially-abandoned rows are skipped.

Usage:
    python scripts/convert_golden_set.py
"""

import json
import pandas as pd

LABELS_CSV = "eval/labeling_template.csv"
THREADS_TXT = "eval/threads_to_read.txt"
OUT_JSONL = "eval/golden_set.jsonl"


def load_thread_texts(path: str) -> dict:
    """Parse threads_to_read.txt back into {conversation_id: thread_text}."""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = content.split("=== conversation_id: ")
    thread_map = {}
    for block in blocks[1:]:  # first split chunk is empty/preamble
        header, _, body = block.partition(" ===")
        conv_id = header.strip()
        thread_map[conv_id] = body.strip()
    return thread_map


def main():
    df = pd.read_csv(LABELS_CSV, encoding="utf-8-sig")
    thread_map = load_thread_texts(THREADS_TXT)

    # Only keep rows with the core required fields filled in
    required = ["intent", "severity", "handling_strategy"]
    labeled = df.dropna(subset=required, how="any")
    labeled = labeled[(labeled[required] != "").all(axis=1)]

    written = 0
    with open(OUT_JSONL, "w", encoding="utf-8") as out_f:
        for _, row in labeled.iterrows():
            conv_id = str(row["conversation_id"]).replace(".0", "")
            thread_text = thread_map.get(conv_id, thread_map.get(str(row["conversation_id"]), ""))

            record = {
                "conversation_id": conv_id,
                "thread_text": thread_text,
                "intent": row.get("intent", ""),
                "severity": row.get("severity", ""),
                "handling_strategy": row.get("handling_strategy", ""),
                "privacy_requirement": row.get("privacy_requirement", ""),
                "automation_eligibility": row.get("automation_eligibility", ""),
                "reason": row.get("reason", ""),
                "reference_reply_notes": row.get("reference_reply_notes", ""),
                "labeler_notes": row.get("labeler_notes", ""),
            }
            # Replace NaN with empty string for clean JSON
            record = {k: ("" if pd.isna(v) else v) for k, v in record.items()}

            out_f.write(json.dumps(record, ensure_ascii=False) + "\n")
            written += 1

    print(f"Wrote {written} labeled examples to {OUT_JSONL}")


if __name__ == "__main__":
    main()