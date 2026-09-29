{{ config(unique_key='signal_id') }}
-- Union of receipted signals from both sources, resolved to account_id. The contract check lives here:
-- anything without an https:// source_url stays in RAW and is counted in raw.ingest_rejects by the loader.

with sb as (
  select
    'sb:' || event_key                              as signal_id,
    ids.account_id,
    case s.signal_type
      when 'vendor_change' then 'vendor_change'
      when 'cost' then 'cost_program'
      when 'cost_cutting' then 'cost_program'
      when 'efficiency' then 'cost_program'
      when 'leadership_change' then 'leadership_change'
      when 'hiring' then 'finance_hiring'
      when 'expansion' then 'expansion'
      when 'geo' then 'expansion'
      when 'headcount' then 'headcount_growth'
      else 'other' end                              as signal_type,
    s.quote,
    coalesce(s.receipt_url, s.source_url)           as source_url,
    s.page_ref,
    s.event_date,
    case when s.verified then 1 else 2 end          as evidence_tier,
    s.verified,
    'steadybase'                                    as source,
    s.event_key,
    s.first_seen,
    s._loaded_at
  from {{ source('raw', 'steadybase_signals') }} s
  join {{ ref('account_ids') }} ids on ids.id_type = 'ticker' and ids.id_value = s.ticker
  where coalesce(s.receipt_url, s.source_url) like 'https://%'
),
clay as (
  select
    'clay:' || c.play || ':' || c.source_row_id     as signal_id,
    ids.account_id,
    c.signal_type,
    c.artifact_text                                 as quote,
    c.artifact_url                                  as source_url,
    null                                            as page_ref,
    c.event_date,
    c.evidence_tier,
    false                                           as verified,
    'clay'                                          as source,
    null                                            as event_key,
    c.received_at                                   as first_seen,
    c._loaded_at
  from {{ source('raw', 'clay_rows') }} c
  join {{ ref('account_ids') }} ids on ids.id_type = 'domain' and ids.id_value = c.domain
  where c.artifact_url like 'https://%' and c.signal_type is not null
)
select * from sb
union all
select * from clay
{% if is_incremental() %}
  where _loaded_at > (select coalesce(max(_loaded_at), '1900-01-01') from {{ this }})
{% endif %}
