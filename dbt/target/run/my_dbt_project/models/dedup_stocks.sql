
  
    

    create or replace table `finflow-455108`.`my_dataset`.`final_table_stocks_clean`
    
    
    OPTIONS()
    as (
      

WITH casted AS (
  SELECT
    symbol,
    SAFE.PARSE_TIMESTAMP('%Y-%m-%d %H:%M:%S', timestamp) AS ts_parsed,
    SAFE_CAST(open   AS FLOAT64) AS open_price,
    SAFE_CAST(high   AS FLOAT64) AS high_price,
    SAFE_CAST(low    AS FLOAT64) AS low_price,
    SAFE_CAST(close  AS FLOAT64) AS close_price,
    SAFE_CAST(volume AS INT64)   AS volume,
    data_type
  FROM `finflow-455108`.`my_dataset`.`bigquery_data`
  WHERE data_type = 'equity'
),
ranked AS (
  SELECT
    symbol,
    ts_parsed,
    open_price,
    high_price,
    low_price,
    close_price,
    volume,
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
    DATE(ts_parsed) AS date_parsed,  -- For partitioning
    open_price  AS open,
    high_price  AS high,
    low_price   AS low,
    close_price AS close,
    volume
  FROM ranked
  WHERE rn = 1
)

SELECT
  symbol,
  ts_parsed           AS timestamp,
  date_parsed,        
  open,
  high,
  low,
  close,
  volume
FROM final
    );
  