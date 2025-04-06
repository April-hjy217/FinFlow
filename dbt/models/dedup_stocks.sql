{{ config(
    materialized='table',   
    alias='final_table_stocks_clean'
)}}

WITH ranked AS (
  SELECT
    symbol,
    timestamp,
    open,
    high,
    low,
    close,
    volume,
    ROW_NUMBER() OVER (
      PARTITION BY symbol, timestamp
      ORDER BY timestamp
    ) AS rn
  FROM  {{ source('my_source', 'final_table_stocks') }}
)
SELECT
  symbol,
  timestamp,
  open,
  high,
  low,
  close,
  volume
FROM ranked
WHERE rn = 1
