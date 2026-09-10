# Taxonomy: Intent, Severity, Handling Strategy

This document is the human-readable reference for the schema defined in code at
`src/schema.py`. Use this while hand-labeling the golden set. If you find an
example that doesn't fit cleanly, don't force it — note it, and consider
whether the taxonomy needs to evolve (log the change and reasoning in
`decision_log.md`).

## Why three separate layers?

Early drafts mapped intent directly to a handling strategy (e.g. "baggage
issues -> DM_REDIRECT"). This breaks down immediately: "lost my sunglasses"
and "lost my child's medication" are both BAGGAGE_LOST_ITEM, but should never
receive the same handling. Decoupling *what the customer wants* (Intent) from
*how bad it is* (Severity) from *what we do about it* (Handling) avoids an
exploding, brittle taxonomy and lets the same intent route differently based
on context.

We also deliberately do NOT use Delta's historical Twitter replies as ground
truth for "correct" handling. The data shows real escalation-worthy situations
(e.g. an 8-hour tarmac wait, a passenger bumped from 5 consecutive flights)
that received the same generic DM-redirect as routine issues. Historical
behavior is observed operational behavior, not necessarily ideal behavior —
our escalation criteria are defined independently and justified below.

---

## Intent — what does the customer want?

| Intent | Description | Example |
|---|---|---|
| `FLIGHT_DELAY_CANCEL` | Delay, cancellation, missed connection, tarmac hold | "8hrs waiting for them to replace a window" |
| `INVOLUNTARY_DISRUPTION` | Denied boarding / bumping — not a voluntary change | "5th consecutive flight my wife and I have been bumped" |
| `BAGGAGE_LOST_ITEM` | Lost, delayed, or damaged baggage/items | "boyfriend left a fanny pack on our flight" |
| `BAGGAGE_FEE_DISPUTE` | Disputing a baggage charge, not a lost-item claim | "how can you allow luggage for baby one way and not on return" |
| `BOOKING_CHANGE_REQUEST` | Voluntary date/seat/name change, rebooking | "looking to change my reward flight last minute" |
| `REFUND_COMPENSATION` | Requesting money back, vouchers, comp for disruption | "4.5 hr delay... no compensation offered" |
| `CHECKIN_BOARDING_ISSUE` | App/kiosk problems, boarding pass, gate/security lines | "TSA lines are at least 2 hours long" |
| `ACCOUNT_SKYMILES_ACCESS` | Login issues, locked account, miles/points questions | "trying to log into account... locked from too many login attempts" |
| `POLICY_FEE_INQUIRY` | Fee/rule/policy question, no personal account issue | "what is Delta's charge for changing return flight date?" |
| `INFLIGHT_SERVICE_COMPLAINT` | In-cabin experience: crew, entertainment, comfort | "electrical outlets at the seats... none of them work" |
| `SERVICE_FEEDBACK_POSITIVE` | Compliment, thanks, no action needed | "shoutout to Delta for helping me get home" |
| `GENERAL_VENT_NO_ACTION` | Frustration/complaint with no actionable request | "I need to learn to never fly Delta" |
| `NOISE_OTHER_AIRLINE` | Delta incidental; another airline is the real subject | "@SouthwestAir does that airline have assigned seats yet" (Delta only tagged) |
| `NOISE_UNRELATED` | Spam, unrelated content, unparseable | — |

**Ambiguity note:** if a message could fit two intents (e.g. a delay tweet
that also demands a refund), label the *primary* ask — the thing the customer
most wants addressed right now. Use the decision log to note any cases where
this call was genuinely close.

---

## Severity / Risk — how serious or urgent is the situation?

| Level | Criteria |
|---|---|
| `LOW` | Routine, no real harm, easily resolved |
| `MEDIUM` | Real inconvenience, single disruption, moderate frustration |
| `HIGH` | ≥2 consecutive disruptions, 4+ hr operational delay/stall, stranded passenger, repeated service failure, serious accessibility issue |
| `CRITICAL` | **Active/unresolved** safety, security, or TSA issue; **active/unresolved** medical emergency; lost medication/passport that is needed imminently (e.g. before a flight departs) |

**Important distinction:** `CRITICAL` requires the situation to be active and unresolved right now — not just a mention of a medical topic. A calm, advance question about policy (e.g. "can I bring my child's medication through security, will it be refrigerated in-flight?") is a `POLICY_FEE_INQUIRY`, not `CRITICAL`, because there's no active emergency — the customer is planning ahead, not in crisis. By contrast, "my daughter's insulin was left behind at security and our flight boards in 20 minutes" is `CRITICAL`, since the harm is imminent and unresolved.

When labeling, ask: *is something actively going wrong right now, or is this a question about a hypothetical/future situation?* Only the former qualifies as CRITICAL on medical/safety grounds.

Severity signals compose — a message can trigger HIGH or CRITICAL through any
one of several independent signals, not a fixed checklist. When labeling,
write down *which* signal(s) applied; this becomes the "reason" field.

---

## Handling Strategy — what should the system do?

| Strategy | When |
|---|---|
| `FULL_AUTO_REPLY` | System can fully resolve publicly — policy Q&A, acknowledgment/thanks — no account access or sensitive data needed |
| `DM_REDIRECT` | Needs account-specific action but is routine/low-risk — triage to DM |
| `HUMAN_ESCALATION` | HIGH/CRITICAL severity, or a DM_REDIRECT case that's gone unresolved or repeated |
| `IGNORED_FILTERED` | Noise — no real support content |

**Important constraint:** the system must never claim a resolution it can't
actually perform (e.g. "your refund has been issued," "we found your bag").
Public replies should realistically triage sensitive/account-specific matters
to DM rather than fabricate an outcome. This is enforced both in reply
generation and explicitly penalized by the LLM-as-judge (see
`eval/judge.py` — "operational realism" dimension).

---

## Supporting fields

- **Privacy requirement** (`NONE` / `REQUIRED`): does this case involve
  sensitive/account-specific info that must not be requested or exposed
  publicly?
- **Automation eligibility** (`FULL` / `LIMITED` / `NONE`): can the system
  safely auto-resolve, only draft/triage, or does it require a human
  regardless of what's drafted?

Every labeled example (and every model decision) should preserve all of
these fields individually, not just a final handling label — this is what
makes failure analysis diagnosable layer-by-layer instead of a black box.