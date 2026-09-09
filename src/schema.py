"""
Core taxonomy for the Delta support agent.

Three independent layers, deliberately decoupled:
    Intent            -> what does the customer want?
    Severity           -> how serious/urgent is the situation?
    HandlingStrategy   -> what should the system actually do?

Do NOT hardcode a 1:1 mapping from Intent to HandlingStrategy.
The same intent can require different handling depending on severity
(e.g. BAGGAGE_LOST_ITEM: lost sunglasses vs. lost medication).

See docs/taxonomy.md for full definitions, rationale, and examples.
"""

from enum import Enum


class Intent(str, Enum):
    FLIGHT_DELAY_CANCEL = "FLIGHT_DELAY_CANCEL"          # delay, cancellation, missed connection, tarmac hold
    INVOLUNTARY_DISRUPTION = "INVOLUNTARY_DISRUPTION"    # denied boarding / bumping, not a voluntary change
    BAGGAGE_LOST_ITEM = "BAGGAGE_LOST_ITEM"              # lost, delayed, or damaged baggage/items
    BAGGAGE_FEE_DISPUTE = "BAGGAGE_FEE_DISPUTE"          # disputing a baggage charge (not a lost-item claim)
    BOOKING_CHANGE_REQUEST = "BOOKING_CHANGE_REQUEST"    # voluntary date/seat/name change, rebooking
    REFUND_COMPENSATION = "REFUND_COMPENSATION"          # requesting money back, vouchers, comp for disruption
    CHECKIN_BOARDING_ISSUE = "CHECKIN_BOARDING_ISSUE"    # app/kiosk problems, boarding pass, gate/security lines
    ACCOUNT_SKYMILES_ACCESS = "ACCOUNT_SKYMILES_ACCESS"  # login issues, locked account, miles/points questions
    POLICY_FEE_INQUIRY = "POLICY_FEE_INQUIRY"            # questions about fees/rules/policy, no personal issue
    INFLIGHT_SERVICE_COMPLAINT = "INFLIGHT_SERVICE_COMPLAINT"  # in-cabin experience: crew, entertainment, comfort
    SERVICE_FEEDBACK_POSITIVE = "SERVICE_FEEDBACK_POSITIVE"    # compliments, thanks, no action needed
    GENERAL_VENT_NO_ACTION = "GENERAL_VENT_NO_ACTION"    # frustration/complaint with no actionable request
    NOISE_OTHER_AIRLINE = "NOISE_OTHER_AIRLINE"          # Delta incidental; another airline is the real subject
    NOISE_UNRELATED = "NOISE_UNRELATED"                  # spam, unrelated content, unparseable


class Severity(str, Enum):
    LOW = "LOW"            # routine, no real harm, easily resolved
    MEDIUM = "MEDIUM"      # real inconvenience, single disruption, moderate frustration
    HIGH = "HIGH"          # >=2 consecutive disruptions, 4+ hr delay/stall, stranded passenger,
                            # repeated service failure, serious accessibility issue
    CRITICAL = "CRITICAL"  # safety/security/TSA issue, medical issue, lost medication/passport


class HandlingStrategy(str, Enum):
    FULL_AUTO_REPLY = "FULL_AUTO_REPLY"        # system can fully resolve publicly, no account/sensitive data needed
    DM_REDIRECT = "DM_REDIRECT"                # needs account-specific action but routine/low-risk -> triage to DM
    HUMAN_ESCALATION = "HUMAN_ESCALATION"      # high/critical severity, or unresolved/repeated DM_REDIRECT case
    IGNORED_FILTERED = "IGNORED_FILTERED"      # noise, no real support content


class PrivacyRequirement(str, Enum):
    NONE = "NONE"          # no sensitive data involved
    REQUIRED = "REQUIRED"  # response must not expose/request sensitive info publicly; must route to DM


class AutomationEligibility(str, Enum):
    FULL = "FULL"          # safe for the system to fully auto-resolve
    LIMITED = "LIMITED"    # system can triage/draft but should not claim resolution
    NONE = "NONE"          # requires a human regardless of drafted response


class Decision:
    """
    Full intermediate decision record for one customer message.
    Preserve every field -- not just the final handling label -- so
    failures can be diagnosed layer by layer (see decision_log.md).
    """

    def __init__(
        self,
        intent: Intent,
        severity: Severity,
        handling: HandlingStrategy,
        privacy: PrivacyRequirement,
        automation: AutomationEligibility,
        reason: str,
    ):
        self.intent = intent
        self.severity = severity
        self.handling = handling
        self.privacy = privacy
        self.automation = automation
        self.reason = reason  # human-readable justification, required for every decision

    def to_dict(self):
        return {
            "intent": self.intent.value,
            "severity": self.severity.value,
            "handling": self.handling.value,
            "privacy_requirement": self.privacy.value,
            "automation_eligibility": self.automation.value,
            "reason": self.reason,
        }