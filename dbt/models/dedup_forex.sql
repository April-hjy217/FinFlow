{{ config(
    materialized='table',
    alias='final_table_forex_clean',
    partition_by = {
      "field": "date_parsed", 
      "data_type": "DAY"
    }
)}}

WITH casted AS (
  SELECT
    symbol,
    SAFE.PARSE_TIMESTAMP('%Y-%m-%d-%H-%M', timestamp) AS ts_parsed,

    SAFE_CAST(low AS FLOAT64)   AS exchange_rate,
    SAFE_CAST(high AS FLOAT64)  AS high_price,
    SAFE_CAST(open AS FLOAT64)  AS open_price,
    SAFE_CAST(close AS FLOAT64) AS close_price,

    data_type
  FROM {{ source('my_source', 'bigquery_data') }}
  WHERE data_type = 'forex'
),
ranked AS (
  SELECT
    symbol,
    ts_parsed,
    exchange_rate,
    high_price,
    open_price,
    close_price,
    ROW_NUMBER() OVER (
      PARTITION BY symbol, ts_parsed
      ORDER BY ts_parsed
    ) AS rn
  FROM casted
),
final AS (
  SELECT
    symbol,
    ts_parsed,
    DATE(ts_parsed) AS date_parsed,
    exchange_rate,
    high_price,
    open_price,
    close_price
  FROM ranked
  WHERE rn = 1
)

SELECT
  symbol,
  ts_parsed         AS local_timestamp,
  date_parsed,      
  exchange_rate,
  high_price,
  open_price,
  close_price
FROM final
