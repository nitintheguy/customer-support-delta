"""
Drafts a customer-facing reply, grounded in similar historical resolutions,
respecting the handling strategy decided by classify.py.

Critical constraint (see docs/taxonomy.md): the drafted reply must NEVER
claim a resolution the system can't actually perform (refund issued, bag
found, account fixed) -- it can only draft what a human agent would
plausibly say at the DM_REDIRECT / HUMAN_ESCALATION / FULL_AUTO_REPLY stage,
not fabricate an outcome.
"""

from src.schema import Decision, HandlingStrategy
from src.llm_client import call_llm_json
from src.retrieve import retrieve_similar_threads

SYSTEM_PROMPT = """You are drafting a public Twitter reply for Delta Air Lines' customer support team.

You will be given:
- The customer's message
- A classification decision (intent, severity, handling strategy, privacy requirement)
- 1-3 similar historical threads showing how Delta has handled similar cases before

Write a short, professional, empathetic reply that matches Delta's real tone (seen in the
historical examples), following the HANDLING STRATEGY exactly:

- FULL_AUTO_REPLY: fully answer the question/acknowledge the feedback publicly. No DM needed.
- DM_REDIRECT: acknowledge the issue, ask the customer to DM their confirmation/ticket number.
  Do NOT attempt to resolve the specific issue yourself in this reply.
- HUMAN_ESCALATION: acknowledge the seriousness, reassure a human will follow up urgently,
  ask for necessary details via DM if appropriate. Do NOT promise a specific resolution or
  timeline you cannot guarantee.
- IGNORED_FILTERED: return an empty reply (this message doesn't need a response).

ABSOLUTE RULE: Never claim an action has already been completed (e.g. "your refund has been
issued", "we found your bag", "your account has been fixed") unless the historical examples
show that information was already confirmed as fact. If in doubt, acknowledge and redirect
rather than inventing an outcome.

Respond with ONLY a JSON object, no other text:
{
  "reply_text": "<the drafted reply, or empty string if IGNORED_FILTERED>",
  "grounding_notes": "<1 sentence on which historical pattern this reply follows>"
}
"""


def draft_reply(customer_message: str, decision: Decision, top_k: int = 2) -> dict:
    if decision.handling == HandlingStrategy.IGNORED_FILTERED:
        return {"reply_text": "", "grounding_notes": "Filtered as noise, no reply needed."}

    similar = retrieve_similar_threads(customer_message, top_k=top_k)
    examples_text = "\n\n".join(
        f"Historical example (similarity={ex['similarity']:.2f}):\n{ex['thread_text']}"
        for ex in similar
    )

    user_prompt = f"""Customer message: {customer_message}

Classification:
- Intent: {decision.intent.value}
- Severity: {decision.severity.value}
- Handling strategy: {decision.handling.value}
- Privacy requirement: {decision.privacy.value}

Similar historical examples:
{examples_text}

Draft the reply now."""

    result = call_llm_json(SYSTEM_PROMPT, user_prompt)
    return result


if __name__ == "__main__":
    from src.classify import classify_thread
    from src.schema import Decision

    test_message = "my flight got delayed and I missed my connection, what can I do"
    decision = classify_thread(test_message)
    print("Classification:", decision.to_dict())

    reply = draft_reply(test_message, decision)
    print("\nDrafted reply:", reply)