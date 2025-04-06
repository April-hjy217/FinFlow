

WITH ranked AS (
  SELECT
    symbol,
    local_timestamp,
    last_refreshed_utc,
    exchange_rate,
    ROW_NUMBER() OVER (
      PARTITION BY symbol, local_timestamp
      ORDER BY local_timestamp
    ) AS rn
  FROM `finflow-455108`.`my_dataset`.`final_table_forex`
)
SELECT
  symbol,
  local_timestamp,
  last_refreshed_utc,
  exchange_rate
FROM ranked
WHERE rn = 1