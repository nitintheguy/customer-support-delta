"""
Filter the Customer Support on Twitter dataset (twcs.csv) down to
full conversation threads involving Delta (@Delta).

Usage:
    python filter_delta.py twcs.csv delta_threads.csv

Output:
    delta_threads.csv - all tweets belonging to any thread that
    includes at least one tweet from Delta, with an added
    `conversation_id` column so you can group rows back into threads.
"""

import sys
import pandas as pd


def build_thread_ids(df: pd.DataFrame) -> pd.Series:
    """
    Walk each tweet back to the root of its conversation using
    in_response_to_tweet_id, and assign every tweet the root tweet_id
    as its conversation_id. This lets you group full threads together
    even though the raw file only stores parent/child links.
    """
    id_to_parent = dict(zip(df["tweet_id"], df["in_response_to_tweet_id"]))

    root_cache = {}

    def find_root(tweet_id):
        if tweet_id in root_cache:
            return root_cache[tweet_id]

        path = []
        current = tweet_id
        while True:
            path.append(current)
            parent = id_to_parent.get(current)
            # Stop if no parent, parent not in dataset, or NaN
            if pd.isna(parent) or parent not in id_to_parent:
                root = current
                break
            current = parent

        for node in path:
            root_cache[node] = root
        return root

    return df["tweet_id"].apply(find_root)


def main():
    if len(sys.argv) != 3:
        print("Usage: python filter_delta.py <input_csv> <output_csv>")
        sys.exit(1)

    input_path, output_path = sys.argv[1], sys.argv[2]

    print(f"Loading {input_path} ...")
    df = pd.read_csv(input_path)

    print(f"Total rows in dataset: {len(df):,}")

    # Delta's support handle in this dataset is "Delta" (case-sensitive)
    delta_mask = df["author_id"] == "Delta"
    delta_tweet_ids = set(df.loc[delta_mask, "tweet_id"])
    print(f"Tweets authored by Delta: {len(delta_tweet_ids):,}")

    print("Building conversation thread ids (this may take a minute)...")
    df["conversation_id"] = build_thread_ids(df)

    # Find every conversation_id that has at least one Delta tweet in it
    delta_conversations = set(
        df.loc[df["tweet_id"].isin(delta_tweet_ids), "conversation_id"]
    )
    print(f"Distinct Delta conversation threads: {len(delta_conversations):,}")

    result = df[df["conversation_id"].isin(delta_conversations)].copy()

    # Sort so each thread's tweets appear together in order
    result.sort_values(["conversation_id", "tweet_id"], inplace=True)

    result.to_csv(output_path, index=False)
    print(f"Saved {len(result):,} rows across {len(delta_conversations):,} threads to {output_path}")


if __name__ == "__main__":
    main()