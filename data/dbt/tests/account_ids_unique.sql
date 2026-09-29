-- Fails if one identifier is claimed by two accounts. Dedupe on account_id and nothing else, and the id map must be one-to-one.
select id_type, id_value, count(distinct account_id) as n
from {{ ref('account_ids') }}
group by 1, 2
having count(distinct account_id) > 1
