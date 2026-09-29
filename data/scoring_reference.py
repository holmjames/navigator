"""Reference implementation of docs/scoring.md in plain Python.

data/scoring.sql is the production version. This file exists so the arithmetic can be tested without a
warehouse, and so the SQL has something to be checked against. If the two disagree, the SQL is wrong.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Optional

BASE_POINTS = {
    "vendor_change": 30, "cost_program": 26, "leadership_change": 22, "travel_role_hiring": 20,
    "expansion": 18, "funding": 16, "m_and_a": 16, "finance_hiring": 14, "headcount_growth": 10, "other": 6,
}
EVIDENCE = {1: 1.00, 2: 0.85, 3: 0.60}
BUYER_PERSONAS = {"cfo", "controller", "vp_finance", "finance_leadership", "procurement", "travel_manager"}


@dataclass
class Account:
    employees: Optional[int]
    office_countries: int
    office_count: int
    industry_travel_index: int
    stack_detected: str                    # displacement | card_only | none
    headcount_growth_24m: Optional[float]
    is_public: bool
    last_earnings_call_date: Optional[date]
    next_earnings_call_date: Optional[date]
    fiscal_year_end_date: Optional[date]
    closed_lost_timing_18m: bool = False
    former_customer: bool = False


@dataclass
class Signal:
    signal_type: str
    evidence_tier: int
    event_date: date
    source_url: str


@dataclass
class Person:
    persona: str
    role_start: Optional[date]


def fit_employees(n: Optional[int]) -> int:
    if n is None: return 3
    if n < 50: return 1
    if n < 200: return 6
    if n < 1000: return 8
    if n < 5000: return 10
    if n < 20000: return 9
    return 6


def fit_travel(a: Account) -> int:
    c = 6 if a.office_countries >= 4 else 3 if a.office_countries >= 2 else 0
    o = 4 if a.office_count >= 5 else 2 if a.office_count >= 2 else 0
    return c + o + max(0, min(4, a.industry_travel_index))


def fit_stack(s: str) -> int:
    return {"displacement": 10, "card_only": 5}.get(s, 3)


def fit_growth(g: Optional[float]) -> int:
    if g is None: return 2
    if g >= 0.30: return 6
    if g >= 0.15: return 4
    if g >= 0: return 2
    return 0


def fit(a: Account) -> int:
    return fit_employees(a.employees) + fit_travel(a) + fit_stack(a.stack_detected) + fit_growth(a.headcount_growth_24m)


def recency(age_days: int) -> float:
    if age_days <= 14: return 1.00
    if age_days <= 45: return 0.80
    if age_days <= 90: return 0.50
    return 0.0


def signal(signals: list[Signal], today: date) -> int:
    adjusted = sorted(
        (BASE_POINTS.get(s.signal_type, 6) * EVIDENCE.get(s.evidence_tier, 0.6) * recency((today - s.event_date).days)
         for s in signals if s.source_url.startswith("https://") and (today - s.event_date).days <= 90),
        reverse=True,
    )
    if not adjusted: return 0
    top = adjusted[0] + 0.2 * (adjusted[1] if len(adjusted) > 1 else 0)
    return round(min(35.0, top))


def timing(a: Account, people: list[Person], today: date) -> tuple[int, int, int, int]:
    if not a.is_public:
        cal = 3
    elif a.next_earnings_call_date and 0 <= (a.next_earnings_call_date - today).days <= 14:
        cal = 0
    elif a.last_earnings_call_date and 1 <= (today - a.last_earnings_call_date).days <= 28:
        cal = 6
    elif a.last_earnings_call_date and 29 <= (today - a.last_earnings_call_date).days <= 56:
        cal = 3
    else:
        cal = 2
    role = 0
    for p in people:
        if p.persona in BUYER_PERSONAS and p.role_start:
            d = (today - p.role_start).days
            role = max(role, 6 if 30 <= d <= 120 else 3 if 121 <= d <= 180 else 2 if d < 30 else 0)
    fye = 3 if a.fiscal_year_end_date and 60 <= (a.fiscal_year_end_date - today).days <= 120 else 0
    return min(15, cal + role + fye), cal, role, fye


def relationship(a: Account, best_strength: float) -> int:
    pts = 10 if best_strength >= 0.70 else 6 if best_strength >= 0.50 else 3 if best_strength >= 0.30 else 0
    pts += 4 if a.closed_lost_timing_18m else 0
    pts += 4 if a.former_customer else 0
    return min(10, pts)


def priority(score: int) -> str:
    return "P1" if score >= 80 else "P2" if score >= 65 else "P3" if score >= 50 else "P4"


def score(a: Account, signals: list[Signal], people: list[Person], best_strength: float, today: date) -> dict:
    f = fit(a)
    s = signal(signals, today)
    t, cal, role, fye = timing(a, people, today)
    r = relationship(a, best_strength)
    total = f + s + t + r
    return {"fit": f, "signal": s, "timing": t, "relationship": r, "score": total, "priority": priority(total),
            "components": {"fit_employees": fit_employees(a.employees), "fit_travel": fit_travel(a), "fit_stack": fit_stack(a.stack_detected),
                           "fit_growth": fit_growth(a.headcount_growth_24m), "timing_calendar": cal, "timing_role": role, "timing_fye": fye}}
