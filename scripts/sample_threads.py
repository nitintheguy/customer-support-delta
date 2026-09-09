"""
Sample N random full conversation threads from delta_threads.csv and print
them in a readable, chronological format so you can actually read them
like conversations.

Usage:
    python sample_threads.py data/delta_threads.csv --n 40
    python sample_threads.py data/delta_threads.csv --n 40 --seed 42 --out sample_output.txt
"""

import argparse
import sys
import pandas as pd


def format_thread(thread_df: pd.DataFrame) -> str:
    """Format a single thread's tweets in chronological, readable order."""
    thread_df = thread_df.sort_values("tweet_id")
    lines = [f"--- Thread {thread_df['conversation_id'].iloc[0]} ---"]
    for _, row in thread_df.iterrows():
        speaker = "DELTA" if row["author_id"] == "Delta" else f"CUSTOMER({row['author_id']})"
        text = str(row["text"]).replace("\n", " ").strip()
        lines.append(f"[{speaker}] {text}")
    lines.append("")  # blank line between threads
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input_csv", help="Path to delta_threads.csv")
    parser.add_argument("--n", type=int, default=40, help="Number of threads to sample")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    parser.add_argument("--out", type=str, default=None, help="Optional output file path")
    args = parser.parse_args()

    print(f"Loading {args.input_csv} ...")
    df = pd.read_csv(args.input_csv)

    all_conv_ids = df["conversation_id"].unique()
    print(f"Total threads available: {len(all_conv_ids):,}")

    rng = pd.Series(all_conv_ids).sample(n=min(args.n, len(all_conv_ids)), random_state=args.seed)
    sampled_ids = set(rng.tolist())

    output_chunks = []
    for conv_id in sampled_ids:
        thread_df = df[df["conversation_id"] == conv_id]
        # Skip threads with only 1 tweet (not much of a conversation)
        if len(thread_df) < 2:
            continue
        output_chunks.append(format_thread(thread_df))

    full_output = "\n".join(output_chunks)

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(full_output)
        print(f"Wrote {len(output_chunks)} threads to {args.out}")
    else:
        print(full_output)


if __name__ == "__main__":
    main()