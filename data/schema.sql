-- Navigator schema. Snowflake dialect.
-- Three schemas: RAW (append-only, one table per source), CORE (resolved, deduped), MARTS (what the playbook and manager view read).
-- Every table carries _loaded_at. Nothing in RAW is ever updated or deleted.

create schema if not exists raw;
create schema if not exists core;
create schema if not exists marts;

------------------------------------------------------------------------------------------------
-- RAW
------------------------------------------------------------------------------------------------

-- SteadyBase: signals from the tenant views and the delta feed. event_key is the dedupe key.
create table if not exists raw.steadybase_signals (
  event_key        string not null,
  ticker           string,
  account_id_sb    string,          -- SteadyBase acc_<32hex>
  company          string,
  signal_type      string,
  matched_rule     string,
  quote            string,
  why_it_matters   string,          -- derived sentence, never quotable
  source_url       string,
  page_ref         string,
  receipt_url      string,
  event_date       date,
  evidence_tier    string,
  verified         boolean,
  first_seen       timestamp_ntz,
  payload          variant,
  _loaded_at       timestamp_ntz default current_timestamp(),
  primary key (event_key)
);

create table if not exists raw.steadybase_people (
  ticker           string,
  account_id_sb    string,
  full_name        string,
  title            string,
  persona_key      string,
  linkedin_url     string,
  role_start       date,
  source           string,
  source_ref       string,
  first_seen       timestamp_ntz,
  last_seen        timestamp_ntz,
  _loaded_at       timestamp_ntz default current_timestamp()
);

create table if not exists raw.steadybase_events (   -- next earnings calls
  ticker           string,
  event_type       string,
  report_date      date,
  call_time_et     time,
  webcast_url      string,
  ir_page_url      string,
  _loaded_at       timestamp_ntz default current_timestamp()
);

-- Clay: one row per enriched table row, whatever the play. Payload keeps every column.
create table if not exists raw.clay_rows (
  source_row_id    string not null,
  play             string not null,
  domain           string,
  company          string,
  signal_type      string,
  artifact_url     string,          -- job posting, press release, funding announcement
  artifact_text    string,
  event_date       date,
  evidence_tier    number(1),
  payload          variant,
  received_at      timestamp_ntz,
  _loaded_at       timestamp_ntz default current_timestamp(),
  primary key (play, source_row_id)
);

-- Salesforce nightly (native connector). Columns follow the SFDC objects; only the ones Navigator reads are listed.
create table if not exists raw.sfdc_account (
  id string, name string, website string, industry string, numberofemployees number, billingcountry string,
  ownerid string, owner_type__c string, segment__c string, strategic_flag__c boolean, type string,
  navigator_holdout__c boolean, isdeleted boolean, systemmodstamp timestamp_ntz,
  _loaded_at timestamp_ntz default current_timestamp()
);
create table if not exists raw.sfdc_contact (
  id string, accountid string, firstname string, lastname string, title string, email string, phone string,
  mailingcountry string, hasoptedoutofemail boolean, donotcall boolean, linkedin_url__c string,
  isdeleted boolean, systemmodstamp timestamp_ntz,
  _loaded_at timestamp_ntz default current_timestamp()
);
create table if not exists raw.sfdc_opportunity (
  id string, accountid string, stagename string, isclosed boolean, iswon boolean, closedate date,
  loss_reason__c string, ownerid string, createddate timestamp_ntz, systemmodstamp timestamp_ntz,
  _loaded_at timestamp_ntz default current_timestamp()
);
create table if not exists raw.sfdc_task (
  id string, whoid string, whatid string, subject string, status string, activitydate date,
  navigator_touch_id__c string, navigator_draft_id__c string, systemmodstamp timestamp_ntz,
  _loaded_at timestamp_ntz default current_timestamp()
);

-- Apollo events (webhook): opens, replies, bounces, sequence state.
create table if not exists raw.apollo_events (
  event_id         string not null,
  event_type       string,          -- email_sent, email_opened, email_replied, email_bounced, contact_unsubscribed
  contact_email    string,
  sequence_id      string,
  message_id       string,
  reply_text       string,
  occurred_at      timestamp_ntz,
  payload          variant,
  _loaded_at       timestamp_ntz default current_timestamp(),
  primary key (event_id)
);

-- Nooks calls (webhook or nightly export; see integrations/nooks.md).
create table if not exists raw.nooks_calls (
  call_id          string not null,
  rep_email        string,
  contact_phone    string,
  disposition      string,
  duration_sec     number,
  transcript       string,
  started_at       timestamp_ntz,
  payload          variant,
  _loaded_at       timestamp_ntz default current_timestamp(),
  primary key (call_id)
);

-- TheSwarm intro paths (API, weekly per worked account).
create table if not exists raw.swarm_paths (
  target_linkedin  string,
  target_domain    string,
  connector_email  string,
  connector_name   string,
  overlap_type     string,          -- work, school, investor, linkedin, email
  strength         float,
  fetched_at       timestamp_ntz,
  payload          variant,
  _loaded_at       timestamp_ntz default current_timestamp()
);

-- MoltSets enrichment results (called from Clay or n8n).
create table if not exists raw.moltsets_contacts (
  linkedin_url     string,
  full_name        string,
  company_domain   string,
  business_email   string,
  email_risk_score string,          -- A..F
  email_validated_at date,
  mobile           string,
  mobile_verified_at date,
  current_role_start_date date,
  payload          variant,
  _loaded_at       timestamp_ntz default current_timestamp()
);

-- Ingest rejects: anything that failed a contract (no https source_url, no identity, etc.).
create table if not exists raw.ingest_rejects (
  source string, reason string, payload variant, _loaded_at timestamp_ntz default current_timestamp()
);

------------------------------------------------------------------------------------------------
-- CORE
------------------------------------------------------------------------------------------------

create table if not exists core.account (
  account_id               string not null,      -- acc_<32hex>; SteadyBase's for public, minted here for private
  sfdc_id                  string,
  name                     string,
  domain                   string,
  ticker                   string,
  is_public                boolean default false,
  country                  string,
  industry                 string,
  employees                number,
  office_countries         number,
  office_count             number,
  headcount_growth_24m     float,
  stack_detected           string,               -- displacement | card_only | none
  segment                  string,               -- smb | mid_market | enterprise (from SFDC)
  strategic_flag           boolean default false,
  tier                     string,               -- A | B | C, derived (see docs/tiers.md)
  owner_id                 string,
  owner_type               string,               -- bdr | ae | none
  ae_opt_in                boolean default false,
  parent_account_id        string,
  is_customer              boolean default false,
  has_open_opp             boolean default false,
  closed_lost_timing_18m   boolean default false,
  former_customer          boolean default false,
  last_earnings_call_date  date,
  next_earnings_call_date  date,
  fiscal_year_end_date     date,
  resolution_status        string,               -- resolved | ambiguous | conflict | no_match
  holdout                  boolean default false,
  _loaded_at               timestamp_ntz default current_timestamp(),
  primary key (account_id)
);

create table if not exists core.account_ids (
  account_id  string not null,
  id_type     string not null,    -- lei | cik | ticker | exchange_ticker | domain | linkedin_company | legal_name | sfdc_id | duns
  id_value    string not null,
  source      string,
  confidence  float,
  _loaded_at  timestamp_ntz default current_timestamp(),
  primary key (id_type, id_value)  -- the database refuses two accounts claiming one identifier
);

create table if not exists core.contact (
  contact_id          string not null,
  account_id          string not null,
  sfdc_id             string,
  linkedin_url        string,
  first_name          string,
  last_name           string,
  title               string,
  persona             string,        -- cfo | controller | vp_finance | finance_leadership | fpa | treasury | ap | procurement | travel_manager | office_workplace | ea_to_cfo | other
  persona_rank        number,
  seniority           string,
  role_start          date,
  country             string,
  email               string,
  email_grade         string,        -- A..F, null if unverified
  email_validated_at  date,
  mobile              string,
  mobile_verified_at  date,
  source              string,
  dnc                 boolean default false,
  unsubscribed        boolean default false,
  status              string,        -- active | referred | wrong_person | suppressed
  _loaded_at          timestamp_ntz default current_timestamp(),
  primary key (contact_id),
  unique (account_id, linkedin_url)
);

create table if not exists core.signals (
  signal_id      string not null,
  account_id     string not null,
  signal_type    string not null,   -- vendor_change | cost_program | leadership_change | travel_role_hiring | expansion | funding | m_and_a | finance_hiring | headcount_growth | other
  quote          string,            -- verbatim; null only for tier 3
  source_url     string not null,   -- must start with https://
  page_ref       string,
  event_date     date not null,
  evidence_tier  number(1) not null, -- 1 quote | 2 artifact | 3 inferred
  verified       boolean,
  source         string not null,   -- steadybase | clay
  event_key      string,
  first_seen     timestamp_ntz,
  _loaded_at     timestamp_ntz default current_timestamp(),
  primary key (signal_id)
);
-- Snowflake does not enforce CHECK constraints; this one documents intent. The enforcement is the loader's contract check
-- (ingest/SPEC.md) and the dbt test data/dbt/tests/signals_https.sql.
alter table core.signals add constraint if not exists chk_https check (source_url like 'https://%');

create table if not exists core.briefs (
  account_id   string not null,
  brief_json   variant,            -- {why_now, footprint, stack, timing, risk, committee_summary, no_signal:boolean}
  why_now      string,
  sources      array,              -- signal_ids used
  written_at   timestamp_ntz,
  fresh_until  date,
  model        string,
  tokens_in    number,
  tokens_out   number,
  _loaded_at   timestamp_ntz default current_timestamp(),
  primary key (account_id)
);

create table if not exists core.scores (
  account_id       string not null,
  as_of            date not null,
  fit              number, signal number, timing number, relationship number,
  score            number,
  priority         string,          -- P1..P4
  reasons          array,
  weights_version  string,
  fit_employees number, fit_travel number, fit_stack number, fit_growth number,
  timing_calendar number, timing_role number, timing_fye number,
  _loaded_at       timestamp_ntz default current_timestamp(),
  primary key (account_id, as_of)
);

create table if not exists core.drafts (
  draft_id     string not null,
  account_id   string not null,
  contact_id   string,
  channel      string,             -- email | call_opener | linkedin
  subject      string,
  body         string,
  receipts     array,              -- signal_ids the draft cites
  qa_grade     string,
  qa_notes     array,
  model        string,
  version      number,
  created_at   timestamp_ntz,
  _loaded_at   timestamp_ntz default current_timestamp(),
  primary key (draft_id)
);

create table if not exists core.touches (
  touch_id     string not null,
  account_id   string not null,
  contact_id   string,
  channel      string,             -- email | call | linkedin | warm_intro
  draft_id     string,
  qa_grade     string,
  tier         string,
  autonomy     string,             -- auto | approve | research_only
  sent_by      string,             -- agent | rep
  rep_id       string,
  sent_at      timestamp_ntz,
  sequence_id  string,
  signal_id    string,
  play         string,
  _loaded_at   timestamp_ntz default current_timestamp(),
  primary key (touch_id)
);

create table if not exists core.outcomes (
  outcome_id  string not null,
  touch_id    string,
  account_id  string not null,
  contact_id  string,
  kind        string not null,     -- open | reply | call | meeting | opp | bounce | unsubscribe
  class       string,              -- for replies: interested | question | objection | not_now | out_of_office | referral | wrong_person | unsubscribe
  at          timestamp_ntz,
  detail      variant,
  _loaded_at  timestamp_ntz default current_timestamp(),
  primary key (outcome_id)
);

create table if not exists core.warm_paths (
  account_id     string not null,
  contact_id     string,
  connector_id   string,           -- Meridian Travel employee, customer, investor, or advisor
  connector_name string,
  overlap        string,
  strength       float,
  refreshed_at   timestamp_ntz,
  _loaded_at     timestamp_ntz default current_timestamp()
);

create table if not exists core.review_queue (
  row_id       string not null,
  source       string,
  reason       string,             -- ambiguous | conflict | no_match | domain_collision
  input        variant,
  candidates   array,
  resolved_to  string,
  resolved_by  string,
  resolved_at  timestamp_ntz,
  _loaded_at   timestamp_ntz default current_timestamp(),
  primary key (row_id)
);

create table if not exists core.decisions (
  decision_id  string not null,
  account_id   string not null,
  contact_id   string,
  action       string,
  autonomy     string,
  when_at      date,
  reason       string,
  inputs       variant,
  decided_at   timestamp_ntz,
  _loaded_at   timestamp_ntz default current_timestamp(),
  primary key (decision_id)
);

create table if not exists core.geo_rules (
  country             string not null,
  auto_allowed        boolean,
  email_first_allowed boolean,
  calls_allowed       boolean,
  notes               string,
  reviewed_by         string,
  reviewed_at         date,
  primary key (country)
);

create table if not exists core.industry_travel_index (
  industry      string not null,
  travel_index  number(1),        -- 0..4
  primary key (industry)
);

create table if not exists core.switches (
  switch     string not null,      -- tier_a | play:<name> | all
  paused     boolean,
  changed_by string,
  changed_at timestamp_ntz,
  primary key (switch)
);

create table if not exists core.weights (
  weights_version string not null,
  components      variant,             -- the term definitions and thresholds, as data
  fit_on_outcomes number,
  created_by      string,
  created_at      timestamp_ntz default current_timestamp(),
  active          boolean default false,
  activated_by    string,
  activated_at    timestamp_ntz,
  primary key (weights_version)
);

create table if not exists core.cursors (
  source     string not null,          -- steadybase_whats_new | steadybase_bulk_since | swarm_weekly
  cursor     string,
  updated_at timestamp_ntz default current_timestamp(),
  primary key (source)
);

create table if not exists core.geo_rules_staged   like core.geo_rules;
create table if not exists core.play_budgets (
  play           string not null,
  rows_per_month number,
  updated_by     string,
  updated_at     timestamp_ntz default current_timestamp(),
  primary key (play)
);
create table if not exists core.play_budgets_staged like core.play_budgets;

create table if not exists core.operator_tickets (
  ticket      string not null,
  tool        string,
  preview     variant,
  issued_to   string,
  issued_at   timestamp_ntz default current_timestamp(),
  expires_at  timestamp_ntz,
  used_at     timestamp_ntz,
  primary key (ticket)
);

create table if not exists core.audit (
  at         timestamp_ntz default current_timestamp(),
  actor      string,
  action     string,
  target     string,
  detail     variant
);

create table if not exists core.cost_events (
  at          timestamp_ntz default current_timestamp(),
  vendor      string,              -- openai | clay | moltsets | theswarm | steadybase | snowflake
  endpoint    string,
  job         string,              -- brief | draft | qa | reply | reasons | prospect | orchestrator | enrichment
  account_id  string,
  rows        number,
  tokens_in   number,
  tokens_out  number,
  cost_usd    float
);

-- Suppression: one view, used at search time (exclude lists) and before any send.
create or replace view core.v_suppressed as
select account_id, null as contact_id, 'customer' as why from core.account where is_customer
union all
select account_id, null, 'competitor' from core.account where industry = 'competitor'   -- replace with the real rule
union all
select account_id, contact_id, 'dnc' from core.contact where dnc
union all
select account_id, contact_id, 'unsubscribed' from core.contact where unsubscribed
union all
select account_id, contact_id, 'status' from core.contact where status = 'suppressed'
union all
select account_id, null, 'holdout' from core.account where holdout;

------------------------------------------------------------------------------------------------
-- MARTS
------------------------------------------------------------------------------------------------

-- One row per account per rep per day: what the Slack card is built from.
create or replace view marts.playbook_daily as
select
  a.account_id, a.name, a.domain, a.owner_id as rep_id, a.tier, a.segment, a.country,
  s.score, s.priority, s.reasons, s.fit, s.signal, s.timing, s.relationship,
  b.brief_json, b.why_now, b.fresh_until,
  d.decision_id, d.action, d.autonomy, d.when_at, d.reason as decision_reason, d.contact_id,
  dr.draft_id, dr.subject, dr.body, dr.qa_grade, dr.qa_notes,
  c.first_name, c.title, c.persona, c.email_grade, (c.mobile is not null) as has_mobile,
  (select max(strength) from core.warm_paths w where w.account_id = a.account_id) as warm_strength
from core.account a
join core.scores s on s.account_id = a.account_id and s.as_of = current_date
left join core.briefs b on b.account_id = a.account_id
left join core.decisions d on d.account_id = a.account_id
  and d.decided_at = (select max(decided_at) from core.decisions x where x.account_id = a.account_id)
left join core.contact c on c.contact_id = d.contact_id
left join core.drafts dr on dr.account_id = a.account_id and dr.contact_id = d.contact_id
  and dr.version = (select max(version) from core.drafts y where y.account_id = a.account_id and y.contact_id = d.contact_id)
where s.priority in ('P1','P2','P3')
  and not a.holdout
  and a.account_id not in (select account_id from core.v_suppressed where contact_id is null);

-- Manager view: by pod, by play, by tier, by day.
create or replace view marts.manager_daily as
select
  date_trunc('day', t.sent_at) as day,
  t.rep_id, t.play, t.tier, t.autonomy, t.qa_grade,
  count(distinct t.touch_id)                                   as touches,
  count(distinct case when o.kind = 'reply' then o.outcome_id end)   as replies,
  count(distinct case when o.kind = 'meeting' then o.outcome_id end) as meetings
from core.touches t
left join core.outcomes o on o.touch_id = t.touch_id
group by 1,2,3,4,5,6;

-- Signals actioned within 24 hours.
create or replace view marts.actioned_24h as
select
  d.decided_at::date as day,
  count(*) as cards,
  count(case when t.sent_at <= dateadd('hour', 24, d.decided_at) then 1 end) as actioned
from core.decisions d
left join core.touches t on t.account_id = d.account_id and t.sent_at >= d.decided_at
where d.action in ('email','call','linkedin','warm_intro')
group by 1;

-- Cost per meeting.
create or replace view marts.cost_per_meeting as
select
  date_trunc('month', c.at) as month,
  sum(c.cost_usd) as cost_usd,
  (select count(*) from core.outcomes o where o.kind = 'meeting' and date_trunc('month', o.at) = date_trunc('month', c.at)) as meetings,
  sum(c.cost_usd) / nullif((select count(*) from core.outcomes o where o.kind = 'meeting' and date_trunc('month', o.at) = date_trunc('month', c.at)), 0) as cost_per_meeting
from core.cost_events c
group by 1;
