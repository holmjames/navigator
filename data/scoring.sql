-- Navigator scoring, weights v1. Snowflake dialect.
-- Produces one row per account into core.scores. Nightly, and on demand for accounts with new signals.
-- The arithmetic is docs/scoring.md. Larkspur Dynamics (fixture) must come out at 91.

create or replace view core.v_score_inputs as
with acct as (
  select
    a.account_id,
    a.employees,
    a.office_countries,
    a.office_count,
    coalesce(iti.travel_index, 1)                       as industry_travel_index,
    a.stack_detected,                                   -- 'displacement' | 'card_only' | 'none'
    a.headcount_growth_24m,                             -- fraction, e.g. 0.31
    a.is_public,
    a.last_earnings_call_date,
    a.next_earnings_call_date,
    a.fiscal_year_end_date,
    a.closed_lost_timing_18m,                           -- boolean
    a.former_customer                                   -- boolean
  from core.account a
  left join core.industry_travel_index iti on iti.industry = a.industry
  where a.account_id not in (select account_id from core.v_suppressed)
),
fit as (
  select
    account_id,
    case
      when employees is null then 3
      when employees < 50 then 1
      when employees < 200 then 6
      when employees < 1000 then 8
      when employees < 5000 then 10
      when employees < 20000 then 9
      else 6 end                                                     as fit_employees,
    (case when office_countries >= 4 then 6 when office_countries >= 2 then 3 else 0 end)
    + (case when office_count >= 5 then 4 when office_count >= 2 then 2 else 0 end)
    + least(4, greatest(0, industry_travel_index))                   as fit_travel,
    case stack_detected when 'displacement' then 10 when 'card_only' then 5 else 3 end as fit_stack,
    case
      when headcount_growth_24m is null then 2
      when headcount_growth_24m >= 0.30 then 6
      when headcount_growth_24m >= 0.15 then 4
      when headcount_growth_24m >= 0 then 2
      else 0 end                                                     as fit_growth
  from acct
),
sig as (
  select
    s.account_id,
    s.signal_id,
    (case s.signal_type
       when 'vendor_change' then 30
       when 'cost_program' then 26
       when 'leadership_change' then 22
       when 'travel_role_hiring' then 20
       when 'expansion' then 18
       when 'funding' then 16
       when 'm_and_a' then 16
       when 'finance_hiring' then 14
       when 'headcount_growth' then 10
       else 6 end)
    * (case s.evidence_tier when 1 then 1.00 when 2 then 0.85 else 0.60 end)
    * (case
         when datediff('day', s.event_date, current_date) <= 14 then 1.00
         when datediff('day', s.event_date, current_date) <= 45 then 0.80
         when datediff('day', s.event_date, current_date) <= 90 then 0.50
         else 0 end)                                                 as adjusted
  from core.signals s
  where s.source_url like 'https://%'
    and datediff('day', s.event_date, current_date) <= 90
),
sig_ranked as (
  select account_id, adjusted,
         row_number() over (partition by account_id order by adjusted desc) as rn
  from sig
),
sig_agg as (
  select
    account_id,
    least(35, max(case when rn = 1 then adjusted end)
              + 0.2 * coalesce(max(case when rn = 2 then adjusted end), 0)) as signal_pts
  from sig_ranked
  group by account_id
),
persona as (
  -- best new-in-role buyer on the committee
  select account_id,
         min(datediff('day', role_start, current_date)) as days_in_role_min,
         max(case when datediff('day', role_start, current_date) between 30 and 120 then 6
                  when datediff('day', role_start, current_date) between 121 and 180 then 3
                  when datediff('day', role_start, current_date) < 30 then 2
                  else 0 end) as timing_role
  from core.contact
  where persona in ('cfo','controller','vp_finance','finance_leadership','procurement','travel_manager')
    and role_start is not null
  group by account_id
),
timing as (
  select
    a.account_id,
    case
      when not a.is_public then 3
      when a.next_earnings_call_date is not null
           and datediff('day', current_date, a.next_earnings_call_date) between 0 and 14 then 0
      when a.last_earnings_call_date is not null
           and datediff('day', a.last_earnings_call_date, current_date) between 1 and 28 then 6
      when a.last_earnings_call_date is not null
           and datediff('day', a.last_earnings_call_date, current_date) between 29 and 56 then 3
      else 2 end                                                     as timing_calendar,
    coalesce(p.timing_role, 0)                                       as timing_role,
    case when a.fiscal_year_end_date is not null
          and datediff('day', current_date, a.fiscal_year_end_date) between 60 and 120 then 3
         else 0 end                                                  as timing_fye
  from acct a
  left join persona p on p.account_id = a.account_id
),
rel as (
  select
    a.account_id,
    least(10,
      coalesce((select case when max(strength) >= 0.70 then 10
                            when max(strength) >= 0.50 then 6
                            when max(strength) >= 0.30 then 3 else 0 end
                from core.warm_paths w where w.account_id = a.account_id), 0)
      + (case when a.closed_lost_timing_18m then 4 else 0 end)
      + (case when a.former_customer then 4 else 0 end))             as relationship_pts
  from acct a
)
select
  a.account_id,
  f.fit_employees, f.fit_travel, f.fit_stack, f.fit_growth,
  (f.fit_employees + f.fit_travel + f.fit_stack + f.fit_growth)       as fit,
  round(coalesce(s.signal_pts, 0))                                    as signal,
  least(15, t.timing_calendar + t.timing_role + t.timing_fye)        as timing,
  t.timing_calendar, t.timing_role, t.timing_fye,
  r.relationship_pts                                                  as relationship
from acct a
join fit f    on f.account_id = a.account_id
left join sig_agg s on s.account_id = a.account_id
join timing t on t.account_id = a.account_id
join rel r    on r.account_id = a.account_id;

-- Materialize. Reasons are filled by the nightly reason-code job (agents/prompts/reasons.md).
insert into core.scores (account_id, as_of, fit, signal, timing, relationship, score, priority, reasons, weights_version,
                         fit_employees, fit_travel, fit_stack, fit_growth, timing_calendar, timing_role, timing_fye)
select
  account_id,
  current_date,
  fit, signal, timing, relationship,
  fit + signal + timing + relationship                                as score,
  case when fit + signal + timing + relationship >= 80 then 'P1'
       when fit + signal + timing + relationship >= 65 then 'P2'
       when fit + signal + timing + relationship >= 50 then 'P3'
       else 'P4' end                                                  as priority,
  null,
  'v1',
  fit_employees, fit_travel, fit_stack, fit_growth, timing_calendar, timing_role, timing_fye
from core.v_score_inputs;
