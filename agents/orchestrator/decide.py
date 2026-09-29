"""Navigator orchestrator: the next-best-action decision function.

This is the executable form of docs/rules.md. It is a pure function: it takes the account's
state and returns one Decision. It never calls a model, never calls a vendor, never writes.
The caller (the nightly batch or the reply flow) persists the Decision to core.decisions and
acts on it.

Keep it boring. Every rule is a named block with a test in test_decide.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal, Optional

Action = Literal[
    "suppress", "route_to_ae", "expansion_handoff", "review", "wait", "research",
    "warm_intro", "email", "call", "linkedin", "meeting_flow", "human_write",
]
Autonomy = Literal["auto", "approve", "research_only"]

# Caps (docs/tiers.md). Apollo enforces the send cap too; the lower wins.
SENDS_PER_REP_PER_DAY = 40
TOUCHES_PER_CONTACT_PER_WEEK = 2
TOUCHES_PER_ACCOUNT_BEFORE_WAIT = 3
WARM_PATH_THRESHOLD = 0.70
QUIET_PERIOD_DAYS = 14
P4_RESCORE_DELTA = 10

FINANCE_PERSONAS = {"cfo", "controller", "vp_finance", "finance_leadership", "fpa", "treasury", "ap"}
QA_GRADE_ORDER = ["F", "D-", "D", "D+", "C-", "C", "C+", "B-", "B", "B+", "A-", "A", "A+"]


@dataclass
class GeoRule:
    country: str
    auto_allowed: bool = False
    email_first_allowed: bool = False
    calls_allowed: bool = False


@dataclass
class Contact:
    contact_id: str
    persona: str
    persona_rank: int
    country: str
    email_grade: Optional[str] = None       # A..F or None
    role_start: Optional[date] = None
    has_mobile: bool = False
    touches_last_7d: int = 0
    warm_path_strength: float = 0.0
    dnc: bool = False
    unsubscribed: bool = False


@dataclass
class AccountState:
    account_id: str
    priority: str                            # P1..P4
    score: int
    previous_score: Optional[int]
    tier: str                                # A | B | C
    segment: str                             # smb | mid_market | enterprise
    owner_type: str                          # bdr | ae | none
    ae_opt_in: bool
    is_customer: bool
    has_open_opp: bool
    suppressed: bool                         # account-level, from core.v_suppressed
    resolution_status: str                   # resolved | ambiguous | conflict | no_match
    is_public: bool
    next_earnings_call: Optional[date]
    brief_fresh_until: Optional[date]
    rep_sends_today: int
    account_touches_no_reply: int
    last_touch_at: Optional[date]
    last_touch_channel: Optional[str]
    business_days_since_last_touch: int
    qa_grade: Optional[str]                  # grade of the draft that would send, if one exists
    contacts: list[Contact] = field(default_factory=list)
    geo_rules: dict[str, GeoRule] = field(default_factory=dict)
    # reply handling
    reply_class: Optional[str] = None        # interested | question | objection | not_now | out_of_office | referral | wrong_person | unsubscribe
    reply_date_hint: Optional[date] = None   # from not_now / out_of_office


@dataclass
class Decision:
    action: Action
    autonomy: Autonomy
    when: date
    reason: str
    contact_id: Optional[str] = None


def _grade_at_least(grade: Optional[str], floor: str) -> bool:
    if grade is None:
        return False
    return QA_GRADE_ORDER.index(grade) >= QA_GRADE_ORDER.index(floor)


def _business_days_from(start: date, n: int) -> date:
    d = start
    while n > 0:
        d += timedelta(days=1)
        if d.weekday() < 5:
            n -= 1
    return d


def _geo(state: AccountState, country: str) -> GeoRule:
    # An unreviewed country is treated as "approve, no email-first, no calls" (docs/tiers.md).
    return state.geo_rules.get(country, GeoRule(country=country))


def _autonomy(state: AccountState, contact: Contact) -> Autonomy:
    if state.tier == "C":
        return "research_only"
    geo = _geo(state, contact.country)
    if state.tier == "A" and geo.auto_allowed and _grade_at_least(state.qa_grade, "B"):
        return "auto"
    return "approve"


def _effective_rank(c: Contact, today: date) -> float:
    """Persona rank, adjusted for the two things that beat seniority: a strong warm path (two ranks better)
    and being new in role, 30 to 120 days (one rank better). Lower is better. docs/rules.md, Channel choice."""
    rank = float(c.persona_rank)
    if c.warm_path_strength >= WARM_PATH_THRESHOLD:
        rank -= 2
    if c.role_start is not None and 30 <= (today - c.role_start).days <= 120:
        rank -= 1
    return rank


def _best_contact(state: AccountState, today: date) -> Optional[Contact]:
    usable = [c for c in state.contacts if not c.dnc and not c.unsubscribed]
    if not usable:
        return None
    # Effective rank first, then warm-path strength, then a verified channel.
    usable.sort(key=lambda c: (_effective_rank(c, today), -c.warm_path_strength, c.email_grade or "Z"))
    return usable[0]


def decide(state: AccountState, today: date) -> Decision:
    """Return the one thing to do next for this account."""

    # ---- Reply handling comes first: an inbound message changes everything. ----
    if state.reply_class:
        return _decide_reply(state, today)

    # ---- Gates, in order (docs/rules.md) ----
    if state.suppressed:
        return Decision("suppress", "research_only", today, "Account or contact is suppressed.")

    if state.is_customer:
        return Decision("expansion_handoff", "research_only", today,
                        "Active customer: signal routed to the CSM as a note; no BDR touch.")

    if state.has_open_opp:
        return Decision("route_to_ae", "research_only", today,
                        "Open opportunity: signal and brief posted to the AE; the BDR does not touch the account.")

    if state.resolution_status != "resolved":
        return Decision("review", "research_only", today,
                        f"Identity is {state.resolution_status}; nothing is sent to a company we are not sure of.")

    if state.priority == "P4":
        moved = state.previous_score is not None and abs(state.score - state.previous_score) >= P4_RESCORE_DELTA
        if not moved:
            return Decision("wait", "research_only", today + timedelta(days=30), "P4: monitor.")

    contact = _best_contact(state, today)
    if contact is None:
        return Decision("research", "research_only", today, "No contact with a usable channel; prospect research runs.")

    if state.is_public and state.next_earnings_call and contact.persona in FINANCE_PERSONAS:
        days_to_call = (state.next_earnings_call - today).days
        if 0 <= days_to_call <= QUIET_PERIOD_DAYS:
            return Decision("wait", "research_only", _business_days_from(state.next_earnings_call, 2),
                            "Quiet period: finance persona within 14 days of an earnings call; resume two business days after it.",
                            contact.contact_id)

    if state.rep_sends_today >= SENDS_PER_REP_PER_DAY:
        return Decision("wait", "research_only", today + timedelta(days=1), "Rep is at the daily send cap.", contact.contact_id)

    if contact.touches_last_7d >= TOUCHES_PER_CONTACT_PER_WEEK:
        return Decision("wait", "research_only", today + timedelta(days=7), "Contact is at two touches this week.", contact.contact_id)

    if state.account_touches_no_reply >= TOUCHES_PER_ACCOUNT_BEFORE_WAIT:
        return Decision("wait", "research_only", today + timedelta(days=30), "Three touches with no reply; wait 30 days.", contact.contact_id)

    if state.brief_fresh_until is None or state.brief_fresh_until < today:
        return Decision("research", "research_only", today, "Brief is missing or stale; account research runs first.", contact.contact_id)

    if state.owner_type == "ae" and not state.ae_opt_in:
        return Decision("human_write", "research_only", today,
                        "Named account without AE opt-in: research and warm path only.", contact.contact_id)

    autonomy = _autonomy(state, contact)
    if autonomy == "research_only":
        return Decision("human_write", "research_only", today, "Tier C: a human writes every word.", contact.contact_id)

    # ---- Follow-up cadence after a first touch ----
    if state.last_touch_channel and state.account_touches_no_reply >= 1:
        return _decide_follow_up(state, contact, autonomy, today)

    # ---- Channel choice for a first touch ----
    return _decide_channel(state, contact, autonomy, today)


def _decide_channel(state: AccountState, contact: Contact, autonomy: Autonomy, today: date) -> Decision:
    geo = _geo(state, contact.country)
    if contact.warm_path_strength >= WARM_PATH_THRESHOLD:
        return Decision("warm_intro", "approve", today,
                        f"Warm path at {contact.warm_path_strength:.2f}; ask the connector first, email as fallback in 3 business days.",
                        contact.contact_id)
    if _grade_at_least(contact.email_grade, "B") and geo.email_first_allowed:
        return Decision("email", autonomy, today, "Verified email; email first.", contact.contact_id)
    if contact.has_mobile and geo.calls_allowed:
        return Decision("call", "approve", today, "No email-first channel; verified mobile and calls permitted.", contact.contact_id)
    if not geo.email_first_allowed and _grade_at_least(contact.email_grade, "B"):
        return Decision("linkedin", "approve", today, "Country does not allow email-first; LinkedIn note, then email after a reply.", contact.contact_id)
    return Decision("linkedin", "approve", today, "No verified email or mobile; LinkedIn note.", contact.contact_id)


def _decide_follow_up(state: AccountState, contact: Contact, autonomy: Autonomy, today: date) -> Decision:
    geo = _geo(state, contact.country)
    n = state.account_touches_no_reply
    days = state.business_days_since_last_touch
    if n == 1:
        if days < 4:
            return Decision("wait", autonomy, _business_days_from(state.last_touch_at or today, 4), "First touch out; wait 4 business days.", contact.contact_id)
        if contact.has_mobile and geo.calls_allowed:
            return Decision("call", "approve", today, "No reply in 4 business days; call.", contact.contact_id)
        return Decision("email", autonomy, today, "No reply in 4 business days and no mobile; second email, new angle, same receipt.", contact.contact_id)
    if n == 2:
        if days < 5:
            return Decision("wait", autonomy, _business_days_from(state.last_touch_at or today, 5), "Second touch out; wait 5 business days.", contact.contact_id)
        return Decision("linkedin", "approve", today, "Two touches, no reply; LinkedIn note.", contact.contact_id)
    return Decision("wait", autonomy, today + timedelta(days=30), "Three touches, no reply; wait 30 days.", contact.contact_id)


def _decide_reply(state: AccountState, today: date) -> Decision:
    contact = _best_contact(state, today)
    cid = contact.contact_id if contact else None
    rc = state.reply_class
    if rc == "interested":
        return Decision("meeting_flow", "approve", today, "Interested: reply with two times; sequence stopped; contact marked engaged.", cid)
    if rc == "question":
        return Decision("meeting_flow", "approve", today, "Question: answer from the enablement library only; unknowns go to a person.", cid)
    if rc == "objection":
        return Decision("human_write", "research_only", today, "Objection: classified and summarized; a person answers.", cid)
    if rc == "not_now":
        when = state.reply_date_hint or (today + timedelta(days=90))
        return Decision("wait", "approve", when, "Not now: snoozed until the date given, or 90 days.", cid)
    if rc == "out_of_office":
        when = _business_days_from(state.reply_date_hint, 1) if state.reply_date_hint else today + timedelta(days=7)
        return Decision("wait", "approve", when, "Out of office: resend after return.", cid)
    if rc == "referral":
        return Decision("research", "approve", today, "Referral: new contact created; original marked referred.", cid)
    if rc == "wrong_person":
        return Decision("research", "research_only", today, "Wrong person: contact demoted; prospect research reruns.", cid)
    if rc == "unsubscribe":
        return Decision("suppress", "research_only", today, "Unsubscribe: contact suppressed permanently.", cid)
    return Decision("human_write", "research_only", today, f"Unrecognized reply class {rc!r}; a person reads it.", cid)
