"""
Sample threads from delta_threads.csv and produce a labeling template CSV
for building the golden evaluation set.

Each row = one full customer/Delta thread, with the raw conversation text
and empty columns for you to fill in by hand using the taxonomy in
docs/taxonomy.md.

Usage:
    python build_labeling_template.py data/delta_threads.csv --n 220 --out eval/labeling_template.csv
"""

import argparse
import pandas as pd


def format_thread_text(thread_df: pd.DataFrame) -> str:
    thread_df = thread_df.sort_values("tweet_id")
    lines = []
    for _, row in thread_df.iterrows():
        speaker = "DELTA" if row["author_id"] == "Delta" else "CUSTOMER"
        text = str(row["text"]).replace("\n", " ").strip()
        lines.append(f"[{speaker}] {text}")
    return " | ".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv")
    parser.add_argument("--n", type=int, default=220, help="Number of threads to sample for labeling")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--out", type=str, default="eval/labeling_template.csv")
    args = parser.parse_args()

    print(f"Loading {args.input_csv} ...")
    df = pd.read_csv(args.input_csv)

    all_conv_ids = df["conversation_id"].unique()
    sample_ids = pd.Series(all_conv_ids).sample(
        n=min(args.n, len(all_conv_ids)), random_state=args.seed
    )

    rows = []
    for conv_id in sample_ids:
        thread_df = df[df["conversation_id"] == conv_id]
        if len(thread_df) < 1:
            continue
        first_customer_msg = thread_df[thread_df["author_id"] != "Delta"]
        first_customer_text = (
            str(first_customer_msg.iloc[0]["text"]) if len(first_customer_msg) > 0 else ""
        )
        rows.append({
            "conversation_id": conv_id,
            "n_tweets": len(thread_df),
            "first_customer_message": first_customer_text.replace("\n", " ").strip(),
            "full_thread": format_thread_text(thread_df),
            # --- fill these in by hand, using docs/taxonomy.md ---
            "intent": "",
            "severity": "",
            "handling_strategy": "",
            "privacy_requirement": "",
            "automation_eligibility": "",
            "reason": "",
            "reference_reply_notes": "",  # what a good reply should contain/do
            "labeler_notes": "",          # flag anything ambiguous, taxonomy gaps, etc.
        })

    out_df = pd.DataFrame(rows)
    out_df.to_csv(args.out, index=False)
    print(f"Wrote {len(out_df)} threads to label at {args.out}")
    print("Open this in Excel/Sheets and fill in the labeled columns by hand.")


if __name__ == "__main__":
    main()