"""
Runs the full pipeline (classify -> retrieve -> draft_reply) over a batch
of threads and saves results. This is the script the README's "reproduce
headline results" section points to.

Usage:
    python -m src.run_pipeline --input eval/golden_set.jsonl --output outputs/results.jsonl --limit 20
"""

import argparse
import json
import sys
from tqdm import tqdm

from src.classify import classify_thread
from src.draft_reply import draft_reply


def extract_customer_message(thread_text: str) -> str:
    """Pull just the customer-authored lines out of a formatted thread."""
    lines = [l for l in thread_text.split("\n") if l.startswith("[CUSTOMER]")]
    return " ".join(lines) if lines else thread_text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="JSONL file with thread_text per line")
    parser.add_argument("--output", required=True, help="Where to save pipeline results (JSONL)")
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N examples")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        examples = [json.loads(line) for line in f]

    if args.limit:
        examples = examples[: args.limit]

    results = []
    for ex in tqdm(examples, desc="Running pipeline"):
        thread_text = ex["thread_text"]
        customer_message = extract_customer_message(thread_text)

        try:
            decision = classify_thread(thread_text)
            reply = draft_reply(customer_message, decision)
        except Exception as e:
            print(f"Error on conversation_id {ex.get('conversation_id')}: {e}", file=sys.stderr)
            continue

        results.append({
            "conversation_id": ex.get("conversation_id"),
            "predicted_intent": decision.intent.value,
            "predicted_severity": decision.severity.value,
            "predicted_handling": decision.handling.value,
            "predicted_reason": decision.reason,
            "drafted_reply": reply.get("reply_text", ""),
            "grounding_notes": reply.get("grounding_notes", ""),
            # Carry over gold labels for easy comparison in the eval step
            "gold_intent": ex.get("intent", ""),
            "gold_severity": ex.get("severity", ""),
            "gold_handling": ex.get("handling_strategy", ""),
        })

    with open(args.output, "w", encoding="utf-8") as out_f:
        for r in results:
            out_f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"Wrote {len(results)} pipeline results to {args.output}")


if __name__ == "__main__":
    main()