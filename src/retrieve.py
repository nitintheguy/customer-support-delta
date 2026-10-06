"""
Retrieval module: given a new customer message, find similar historical
Delta threads to ground reply drafting in real precedent.

Uses simple TF-IDF + cosine similarity over customer messages in the
full filtered dataset (data/delta_threads.csv) -- lightweight, no extra
infra, fast enough for a subsample, and easy to explain/defend live.

Deliberately NOT using semantic embeddings here: TF-IDF is transparent,
has zero API cost, and is good enough for finding lexically similar
support requests (same keywords/phrasing patterns repeat a lot in this
domain -- "DM your confirmation number", "lost my bag", etc.). This is
a documented design tradeoff -- see decision_log.md.
"""

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

_vectorizer = None
_matrix = None
_threads_df = None
_customer_texts = None


def _build_index(threads_csv: str = "data/delta_threads.csv"):
    global _vectorizer, _matrix, _threads_df, _customer_texts

    df = pd.read_csv(threads_csv)
    _threads_df = df

    # Build one "customer message" text per conversation (concatenate all
    # customer tweets in that thread) to match against
    customer_rows = df[df["author_id"] != "Delta"]
    grouped = customer_rows.groupby("conversation_id")["text"].apply(
        lambda texts: " ".join(str(t) for t in texts)
    )
    _customer_texts = grouped

    _vectorizer = TfidfVectorizer(max_features=5000, stop_words="english")
    _matrix = _vectorizer.fit_transform(grouped.values)


def _ensure_index():
    if _vectorizer is None:
        _build_index()


def get_thread_text(conversation_id, threads_csv: str = "data/delta_threads.csv") -> str:
    """Return the full formatted thread text for a given conversation_id."""
    _ensure_index()
    thread_df = _threads_df[_threads_df["conversation_id"] == conversation_id].sort_values("tweet_id")
    lines = []
    for _, row in thread_df.iterrows():
        speaker = "DELTA" if row["author_id"] == "Delta" else "CUSTOMER"
        lines.append(f"[{speaker}] {row['text']}")
    return "\n".join(lines)


def retrieve_similar_threads(customer_message: str, top_k: int = 3) -> list:
    """
    Given a new customer message, return the top_k most similar historical
    threads (by TF-IDF cosine similarity over customer messages), each as
    {"conversation_id": ..., "similarity": ..., "thread_text": ...}.
    """
    _ensure_index()

    query_vec = _vectorizer.transform([customer_message])
    similarities = cosine_similarity(query_vec, _matrix).flatten()

    top_indices = similarities.argsort()[::-1][:top_k]
    conv_ids = _customer_texts.index[top_indices]

    results = []
    for idx, conv_id in zip(top_indices, conv_ids):
        results.append({
            "conversation_id": conv_id,
            "similarity": float(similarities[idx]),
            "thread_text": get_thread_text(conv_id),
        })
    return results


if __name__ == "__main__":
    # Quick manual test
    test_message = "my flight got delayed and I missed my connection, what can I do"
    results = retrieve_similar_threads(test_message, top_k=3)
    for r in results:
        print(f"--- conversation_id {r['conversation_id']} (similarity={r['similarity']:.3f}) ---")
        print(r["thread_text"][:300])
        print()