-- Singular test: silver_aapl_eod must have exactly one row per
-- (symbol, trade_date). Fails (returns rows) if the merge ever produces
-- duplicates. Avoids depending on dbt_utils so the Flight-embedded copy
-- of this project stays self-contained (no `dbt deps` network fetch).

select symbol, trade_date, count(*) as n
from {{ ref('silver_aapl_eod') }}
group by symbol, trade_date
having count(*) > 1
