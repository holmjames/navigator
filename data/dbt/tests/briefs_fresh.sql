-- Fails if the playbook would show a stale brief. Briefs expire.
select account_id, fresh_until
from {{ ref('playbook_daily') }}
where fresh_until is not null and fresh_until < current_date
