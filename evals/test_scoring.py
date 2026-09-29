"""Scoring reference against the golden numbers. data/scoring.sql must reproduce these."""

import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "data"))
from scoring_reference import Account, Person, Signal, score  # noqa: E402

HERE = Path(__file__).resolve().parent
TODAY = date(2026, 9, 29)


def test_larkspur_scores_91():
    golden = json.load(open(HERE / "golden" / "scores.json"))["acc_larkspur"]
    sigs = [Signal(s["signal_type"], s["evidence_tier"], date.fromisoformat(s["event_date"]), s["source_url"])
            for s in json.load(open(HERE / "fixtures" / "signals.json")) if s["account_id"] == "acc_larkspur"]
    people = [Person(c["persona"], date.fromisoformat(c["role_start"]))
              for c in json.load(open(HERE / "fixtures" / "contacts.json")) if c["account_id"] == "acc_larkspur"]
    a = Account(employees=5200, office_countries=6, office_count=14, industry_travel_index=2, stack_detected="displacement",
                headcount_growth_24m=0.31, is_public=True, last_earnings_call_date=date(2026, 9, 28),
                next_earnings_call_date=date(2026, 11, 5), fiscal_year_end_date=None)
    out = score(a, sigs, people, best_strength=0.82, today=TODAY)
    assert out["score"] == golden["score"] == 91
    assert out["priority"] == "P1"
    assert (out["fit"], out["signal"], out["timing"], out["relationship"]) == (37, 32, 12, 10)
    assert out["components"] == golden["components"]


def test_quiet_period_zeroes_calendar_points():
    a = Account(employees=5200, office_countries=6, office_count=14, industry_travel_index=2, stack_detected="displacement",
                headcount_growth_24m=0.31, is_public=True, last_earnings_call_date=date(2026, 6, 30),
                next_earnings_call_date=date(2026, 10, 5), fiscal_year_end_date=None)
    out = score(a, [], [], 0.0, TODAY)
    assert out["components"]["timing_calendar"] == 0


def test_private_company_gets_flat_calendar_points():
    a = Account(employees=300, office_countries=1, office_count=1, industry_travel_index=1, stack_detected="none",
                headcount_growth_24m=0.05, is_public=False, last_earnings_call_date=None, next_earnings_call_date=None, fiscal_year_end_date=None)
    assert score(a, [], [], 0.0, TODAY)["components"]["timing_calendar"] == 3


def test_tier3_and_http_signals_count_less_or_not_at_all():
    a = Account(employees=300, office_countries=1, office_count=1, industry_travel_index=1, stack_detected="none",
                headcount_growth_24m=0.05, is_public=False, last_earnings_call_date=None, next_earnings_call_date=None, fiscal_year_end_date=None)
    tier3 = [Signal("vendor_change", 3, TODAY, "https://x.example")]
    http = [Signal("vendor_change", 1, TODAY, "http://x.example")]
    assert score(a, tier3, [], 0.0, TODAY)["signal"] == 18   # 30 * 0.6
    assert score(a, http, [], 0.0, TODAY)["signal"] == 0


def test_signal_decays_and_caps():
    a = Account(employees=300, office_countries=1, office_count=1, industry_travel_index=1, stack_detected="none",
                headcount_growth_24m=0.05, is_public=False, last_earnings_call_date=None, next_earnings_call_date=None, fiscal_year_end_date=None)
    old = [Signal("vendor_change", 1, date(2026, 6, 1), "https://x.example")]
    assert score(a, old, [], 0.0, TODAY)["signal"] == 0
    two = [Signal("vendor_change", 1, TODAY, "https://x.example"), Signal("cost_program", 1, TODAY, "https://y.example")]
    assert score(a, two, [], 0.0, TODAY)["signal"] == 35   # 30 + 0.2*26 = 35.2, capped
