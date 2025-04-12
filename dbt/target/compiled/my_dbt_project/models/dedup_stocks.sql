

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
  FROM `finflow-455108`.`my_dataset`.`transformed_data`
  WHERE data_type = 'equity'
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