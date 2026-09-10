"""
Classifies a customer support thread into Intent, Severity, and Handling
Strategy, following the decoupled three-layer taxonomy in docs/taxonomy.md
and src/schema.py.

Usage:
    from src.classify import classify_thread
    decision = classify_thread(thread_text)
    print(decision.to_dict())
"""

from src.schema import Intent, Severity, HandlingStrategy, PrivacyRequirement, AutomationEligibility, Decision
from src.llm_client import call_llm_json

INTENT_VALUES = [i.value for i in Intent]
SEVERITY_VALUES = [s.value for s in Severity]
HANDLING_VALUES = [h.value for h in HandlingStrategy]
PRIVACY_VALUES = [p.value for p in PrivacyRequirement]
AUTOMATION_VALUES = [a.value for a in AutomationEligibility]

SYSTEM_PROMPT = f"""You are a customer support triage system for Delta Air Lines' Twitter support.
Given a customer support conversation thread, classify it along three independent layers.

INTENT (what does the customer want?) - choose exactly one:
{chr(10).join(f"- {v}" for v in INTENT_VALUES)}

SEVERITY (how serious/urgent is the situation?) - choose exactly one:
- LOW: routine, no real harm, easily resolved
- MEDIUM: real inconvenience, single disruption, moderate frustration
- HIGH: >=2 consecutive disruptions, 4+ hr operational delay/stall, stranded passenger,
  repeated service failure, serious accessibility issue
- CRITICAL: an ACTIVE, UNRESOLVED safety/security/TSA issue, an active/unresolved medical
  emergency, or a lost medication/passport needed imminently (e.g. before a flight departs).
  A calm, advance/hypothetical question about a medical or safety-related policy (e.g. "can I
  bring medication through security, will it be refrigerated in-flight?") is NOT critical --
  that is POLICY_FEE_INQUIRY, since nothing is actively going wrong. Only classify CRITICAL
  when something is actively happening right now and unresolved.

IMPORTANT: Severity is independent of intent. The same intent (e.g. BAGGAGE_LOST_ITEM)
can be LOW (lost sunglasses) or CRITICAL (lost medication). Judge severity from the
actual content and stakes described, not from the intent category alone.

HANDLING STRATEGY (what should the system do?) - choose exactly one:
- FULL_AUTO_REPLY: can fully resolve publicly, no account/sensitive data needed
- DM_REDIRECT: needs account-specific action but is routine/low-risk
- HUMAN_ESCALATION: HIGH/CRITICAL severity, or an unresolved/repeated issue
- IGNORED_FILTERED: noise, no real support content

IMPORTANT: Do NOT use what Delta actually replied in the thread as your ground truth
for the correct handling. Historical replies may reflect real operational weaknesses
(e.g. under-escalating serious issues with a generic apology). Decide handling based on
the severity and privacy criteria above, not by imitating what Delta did.

Also determine:
PRIVACY_REQUIREMENT: NONE or REQUIRED (does resolving this need account-specific/sensitive info
that must not be requested or exposed publicly?)
AUTOMATION_ELIGIBILITY: FULL, LIMITED, or NONE (can the system safely auto-resolve, only
draft/triage without claiming resolution, or does it require a human regardless?)

Respond with ONLY a JSON object, no other text, no markdown fences, in this exact shape:
{{
  "intent": "<one of the intent values>",
  "severity": "<one of the severity values>",
  "handling_strategy": "<one of the handling values>",
  "privacy_requirement": "<NONE or REQUIRED>",
  "automation_eligibility": "<FULL, LIMITED, or NONE>",
  "reason": "<one or two sentences: which specific signal(s) drove the severity call, and why this handling follows>"
}}
"""


def classify_thread(thread_text: str, model: str = None) -> Decision:
    user_prompt = f"Classify this Delta support thread:\n\n{thread_text}"

    kwargs = {"model": model} if model else {}
    result = call_llm_json(SYSTEM_PROMPT, user_prompt, **kwargs)

    # Validate against the schema; raise clearly if the model returned something invalid
    try:
        intent = Intent(result["intent"])
        severity = Severity(result["severity"])
        handling = HandlingStrategy(result["handling_strategy"])
        privacy = PrivacyRequirement(result["privacy_requirement"])
        automation = AutomationEligibility(result["automation_eligibility"])
    except (KeyError, ValueError) as e:
        raise ValueError(f"Model returned invalid classification: {result}") from e

    return Decision(
        intent=intent,
        severity=severity,
        handling=handling,
        privacy=privacy,
        automation=automation,
        reason=result.get("reason", ""),
    )


if __name__ == "__main__":
    # Quick manual test against one of our calibration examples
    sample_thread = """
    [CUSTOMER] @Delta 2 year old daughter was prescribed a liquid medication
    that requires it to be refrigerated. Am I allowed to take it in a cooler
    through security, and will the flight crew refrigerate it?
    """
    decision = classify_thread(sample_thread)
    print(decision.to_dict())