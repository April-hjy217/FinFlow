{{ config(
    materialized='table',
    alias='final_table_forex_clean'
)}}

WITH ranked AS (
  SELECT
    symbol,
    timestamp as local_timestamp,
    open as exchange_rate,
    ROW_NUMBER() OVER (
      PARTITION BY symbol, timestamp
      ORDER BY timestamp
    ) AS rn
  FROM {{ source('my_source', 'transformed_data') }}
  WHERE data_type = 'forex'
)
SELECT
  symbol,
  local_timestamp,
  exchange_rate
FROM ranked
WHERE rn = 1
