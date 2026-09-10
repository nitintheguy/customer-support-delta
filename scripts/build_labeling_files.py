"""
Produces two separate files for labeling, instead of one wide spreadsheet:

1. A readable .txt file with full thread text, one block per thread,
   clearly marked with conversation_id -- for reading.
2. A minimal labeling CSV with just conversation_id + label columns --
   for data entry. No long text columns to fight with in Excel.

Usage:
    python build_labeling_files.py data/delta_threads.csv --n 220 \
        --text_out eval/threads_to_read.txt \
        --labels_out eval/labeling_template.csv
"""

import argparse
import pandas as pd


def format_thread(thread_df: pd.DataFrame) -> str:
    thread_df = thread_df.sort_values("tweet_id")
    lines = [f"=== conversation_id: {thread_df['conversation_id'].iloc[0]} ==="]
    for _, row in thread_df.iterrows():
        speaker = "DELTA" if row["author_id"] == "Delta" else "CUSTOMER"
        text = str(row["text"]).replace("\n", " ").strip()
        lines.append(f"[{speaker}] {text}")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("--n", type=int, default=220)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--text_out", type=str, default="eval/threads_to_read.txt")
    parser.add_argument("--labels_out", type=str, default="eval/labeling_template.csv")
    args = parser.parse_args()

    print(f"Loading {args.input_csv} ...")
    df = pd.read_csv(args.input_csv)

    all_conv_ids = df["conversation_id"].unique()
    sample_ids = pd.Series(all_conv_ids).sample(
        n=min(args.n, len(all_conv_ids)), random_state=args.seed
    )

    text_blocks = []
    label_rows = []

    for conv_id in sample_ids:
        thread_df = df[df["conversation_id"] == conv_id]
        if len(thread_df) < 1:
            continue
        text_blocks.append(format_thread(thread_df))
        label_rows.append({
            "conversation_id": conv_id,
            "intent": "",
            "severity": "",
            "handling_strategy": "",
            "privacy_requirement": "",
            "automation_eligibility": "",
            "reason": "",
            "reference_reply_notes": "",
            "labeler_notes": "",
        })

    with open(args.text_out, "w", encoding="utf-8") as f:
        f.write("\n".join(text_blocks))
    print(f"Wrote {len(text_blocks)} readable threads to {args.text_out}")

    labels_df = pd.DataFrame(label_rows)
    labels_df.to_csv(args.labels_out, index=False, encoding="utf-8-sig")
    print(f"Wrote minimal labeling sheet ({len(labels_df)} rows) to {args.labels_out}")
    print("Open threads_to_read.txt to read, labeling_template.csv to fill in labels by conversation_id.")


if __name__ == "__main__":
    main()