"""Tests are the authoritative reading of docs/rules.md. One test per rule."""

from datetime import date, timedelta

import pytest

from decide import AccountState, Contact, GeoRule, decide

TODAY = date(2026, 9, 29)  # a Tuesday

US = GeoRule("US", auto_allowed=True, email_first_allowed=True, calls_allowed=True)
CA = GeoRule("CA", auto_allowed=True, email_first_allowed=True, calls_allowed=True)
GB = GeoRule("GB", auto_allowed=False, email_first_allowed=True, calls_allowed=True)
DE = GeoRule("DE", auto_allowed=False, email_first_allowed=False, calls_allowed=True)
GEO = {g.country: g for g in (US, CA, GB, DE)}


def controller(**kw) -> Contact:
    base = dict(contact_id="c_miguel", persona="controller", persona_rank=2, country="US",
                email_grade="A", has_mobile=True, touches_last_7d=0, warm_path_strength=0.0)
    base.update(kw)
    return Contact(**base)


def larkspur(**kw) -> AccountState:
    """The fixture account, mid-market, tier B, public, fresh brief, no touches yet."""
    base = dict(
        account_id="acc_larkspur", priority="P1", score=91, previous_score=None, tier="B", segment="mid_market",
        owner_type="bdr", ae_opt_in=False, is_customer=False, has_open_opp=False, suppressed=False,
        resolution_status="resolved", is_public=True, next_earnings_call=TODAY + timedelta(days=37),
        brief_fresh_until=TODAY + timedelta(days=13), rep_sends_today=3, account_touches_no_reply=0,
        last_touch_at=None, last_touch_channel=None, business_days_since_last_touch=0, qa_grade="A-",
        contacts=[controller()], geo_rules=GEO,
    )
    base.update(kw)
    return AccountState(**base)


# ---- Gates ----

def test_suppressed_account_gets_no_card():
    d = decide(larkspur(suppressed=True), TODAY)
    assert d.action == "suppress"


def test_customer_goes_to_csm_not_bdr():
    d = decide(larkspur(is_customer=True), TODAY)
    assert d.action == "expansion_handoff"


def test_open_opp_routes_to_ae_instead_of_suppressing():
    d = decide(larkspur(has_open_opp=True), TODAY)
    assert d.action == "route_to_ae"


def test_unresolved_identity_goes_to_review():
    for status in ("ambiguous", "conflict", "no_match"):
        assert decide(larkspur(resolution_status=status), TODAY).action == "review"


def test_p4_waits_unless_score_moved_ten():
    assert decide(larkspur(priority="P4", score=45, previous_score=42), TODAY).action == "wait"
    moved = decide(larkspur(priority="P4", score=48, previous_score=30), TODAY)
    assert moved.action != "wait"


def test_no_usable_contact_triggers_prospect_research():
    d = decide(larkspur(contacts=[]), TODAY)
    assert d.action == "research"
    d = decide(larkspur(contacts=[controller(dnc=True)]), TODAY)
    assert d.action == "research"


def test_quiet_period_defers_finance_persona_until_after_the_call():
    call = TODAY + timedelta(days=9)
    d = decide(larkspur(next_earnings_call=call), TODAY)
    assert d.action == "wait"
    assert d.when > call
    assert (d.when - call).days >= 2


def test_quiet_period_does_not_apply_to_non_finance_persona():
    call = TODAY + timedelta(days=9)
    d = decide(larkspur(next_earnings_call=call, contacts=[controller(persona="travel_manager", persona_rank=9)]), TODAY)
    assert d.action != "wait"


def test_quiet_period_does_not_apply_to_private_companies():
    d = decide(larkspur(is_public=False, next_earnings_call=TODAY + timedelta(days=3)), TODAY)
    assert d.action != "wait"


def test_rep_send_cap():
    d = decide(larkspur(rep_sends_today=40), TODAY)
    assert d.action == "wait" and d.when == TODAY + timedelta(days=1)


def test_contact_weekly_cap():
    d = decide(larkspur(contacts=[controller(touches_last_7d=2)]), TODAY)
    assert d.action == "wait" and d.when == TODAY + timedelta(days=7)


def test_three_touches_no_reply_waits_30_days():
    d = decide(larkspur(account_touches_no_reply=3, last_touch_channel="email", last_touch_at=TODAY - timedelta(days=10),
                        business_days_since_last_touch=8), TODAY)
    assert d.action == "wait" and d.when == TODAY + timedelta(days=30)


def test_stale_brief_forces_research_first():
    assert decide(larkspur(brief_fresh_until=TODAY - timedelta(days=1)), TODAY).action == "research"
    assert decide(larkspur(brief_fresh_until=None), TODAY).action == "research"


def test_named_account_without_opt_in_is_research_only():
    d = decide(larkspur(owner_type="ae", ae_opt_in=False), TODAY)
    assert d.action == "human_write" and d.autonomy == "research_only"


def test_named_account_with_opt_in_proceeds():
    d = decide(larkspur(owner_type="ae", ae_opt_in=True), TODAY)
    assert d.action in ("email", "warm_intro", "call", "linkedin")


# ---- Channel choice ----

def test_warm_path_beats_email():
    d = decide(larkspur(contacts=[controller(warm_path_strength=0.82)]), TODAY)
    assert d.action == "warm_intro" and d.autonomy == "approve"


def test_weak_warm_path_does_not():
    d = decide(larkspur(contacts=[controller(warm_path_strength=0.55)]), TODAY)
    assert d.action == "email"


def test_verified_email_goes_email_first_in_us():
    d = decide(larkspur(), TODAY)
    assert d.action == "email" and d.contact_id == "c_miguel"


def test_bad_email_grade_falls_back_to_call():
    d = decide(larkspur(contacts=[controller(email_grade="D")]), TODAY)
    assert d.action == "call"


def test_no_email_no_mobile_goes_linkedin():
    d = decide(larkspur(contacts=[controller(email_grade=None, has_mobile=False)]), TODAY)
    assert d.action == "linkedin"


def test_germany_is_never_email_first():
    d = decide(larkspur(contacts=[controller(country="DE", email_grade="A", has_mobile=False)]), TODAY)
    assert d.action == "linkedin"


def test_warm_path_and_new_in_role_beat_persona_rank():
    # The Larkspur case from the demo: the CFO outranks the controller, but the controller has a 0.82 warm path
    # and is 58 days into the role. Two ranks for the path, one for new-in-role: the controller wins, by warm intro.
    cfo = controller(contact_id="c_dana", persona="cfo", persona_rank=1, warm_path_strength=0.0)
    ctrl = controller(contact_id="c_miguel", persona="controller", persona_rank=2, warm_path_strength=0.82,
                      role_start=TODAY - timedelta(days=58))
    d = decide(larkspur(contacts=[cfo, ctrl]), TODAY)
    assert d.contact_id == "c_miguel" and d.action == "warm_intro"


def test_persona_rank_wins_when_nothing_else_differs():
    cfo = controller(contact_id="c_dana", persona="cfo", persona_rank=1)
    ctrl = controller(contact_id="c_miguel", persona="controller", persona_rank=2)
    d = decide(larkspur(contacts=[cfo, ctrl]), TODAY)
    assert d.contact_id == "c_dana"


def test_new_in_role_alone_does_not_beat_the_cfo_but_a_warm_path_does():
    cfo = controller(contact_id="c_dana", persona="cfo", persona_rank=1)
    new_ctrl = controller(contact_id="c_miguel", persona="controller", persona_rank=2, role_start=TODAY - timedelta(days=58))
    assert decide(larkspur(contacts=[cfo, new_ctrl]), TODAY).contact_id == "c_dana"   # 1 vs 2-1=1: tie, rank order holds
    warm_ctrl = controller(contact_id="c_miguel", persona="controller", persona_rank=2, warm_path_strength=0.75)
    assert decide(larkspur(contacts=[cfo, warm_ctrl]), TODAY).contact_id == "c_miguel"


# ---- Autonomy ----

def test_tier_a_us_with_good_grade_is_auto():
    d = decide(larkspur(tier="A", segment="smb", qa_grade="B"), TODAY)
    assert d.action == "email" and d.autonomy == "auto"


def test_tier_a_with_low_grade_needs_approval():
    d = decide(larkspur(tier="A", segment="smb", qa_grade="C+"), TODAY)
    assert d.autonomy == "approve"


def test_tier_a_outside_auto_geos_needs_approval():
    d = decide(larkspur(tier="A", segment="smb", qa_grade="A", contacts=[controller(country="GB")]), TODAY)
    assert d.action == "email" and d.autonomy == "approve"


def test_tier_b_always_approve():
    d = decide(larkspur(tier="B", qa_grade="A+"), TODAY)
    assert d.autonomy == "approve"


def test_tier_c_is_human_write():
    d = decide(larkspur(tier="C", segment="enterprise"), TODAY)
    assert d.action == "human_write" and d.autonomy == "research_only"


def test_unreviewed_country_is_approve_and_not_email_first():
    d = decide(larkspur(tier="A", segment="smb", qa_grade="A", contacts=[controller(country="XX", has_mobile=False)]), TODAY)
    assert d.autonomy != "auto"
    assert d.action == "linkedin"


# ---- Follow-ups ----

def test_after_first_email_wait_four_business_days_then_call():
    sent = TODAY - timedelta(days=1)
    early = decide(larkspur(account_touches_no_reply=1, last_touch_channel="email", last_touch_at=sent, business_days_since_last_touch=1), TODAY)
    assert early.action == "wait"
    late = decide(larkspur(account_touches_no_reply=1, last_touch_channel="email", last_touch_at=TODAY - timedelta(days=7), business_days_since_last_touch=5), TODAY)
    assert late.action == "call"


def test_after_first_email_without_mobile_second_email():
    d = decide(larkspur(account_touches_no_reply=1, last_touch_channel="email", last_touch_at=TODAY - timedelta(days=7),
                        business_days_since_last_touch=5, contacts=[controller(has_mobile=False)]), TODAY)
    assert d.action == "email"


def test_after_second_touch_linkedin():
    d = decide(larkspur(account_touches_no_reply=2, last_touch_channel="call", last_touch_at=TODAY - timedelta(days=8),
                        business_days_since_last_touch=6), TODAY)
    assert d.action == "linkedin"


# ---- Replies ----

@pytest.mark.parametrize("cls,action", [
    ("interested", "meeting_flow"), ("question", "meeting_flow"), ("objection", "human_write"),
    ("referral", "research"), ("wrong_person", "research"), ("unsubscribe", "suppress"),
])
def test_reply_classes(cls, action):
    assert decide(larkspur(reply_class=cls), TODAY).action == action


def test_not_now_with_date_snoozes_to_it():
    when = date(2027, 1, 15)
    d = decide(larkspur(reply_class="not_now", reply_date_hint=when), TODAY)
    assert d.action == "wait" and d.when == when


def test_not_now_without_date_snoozes_90_days():
    d = decide(larkspur(reply_class="not_now"), TODAY)
    assert d.action == "wait" and d.when == TODAY + timedelta(days=90)


def test_out_of_office_resends_one_business_day_after_return():
    back = date(2026, 10, 9)  # a Friday
    d = decide(larkspur(reply_class="out_of_office", reply_date_hint=back), TODAY)
    assert d.action == "wait" and d.when == date(2026, 10, 12)  # the Monday


def test_reply_beats_every_gate():
    # Even a suppressed-looking state with a reply gets the reply decision; suppression of the contact happens in the flow.
    d = decide(larkspur(reply_class="interested", rep_sends_today=99), TODAY)
    assert d.action == "meeting_flow"


# ---- Never ----

def test_decide_never_returns_auto_for_eu():
    for country in ("GB", "DE", "FR", "XX"):
        d = decide(larkspur(tier="A", segment="smb", qa_grade="A+", contacts=[controller(country=country)]), TODAY)
        assert d.autonomy != "auto"
