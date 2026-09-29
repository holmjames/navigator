-- Fails if any signal reached CORE without an https:// receipt. Receipted or not stored.
select signal_id, source_url
from {{ ref('signals') }}
where source_url is null or source_url not like 'https://%'
