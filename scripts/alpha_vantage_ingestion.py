import os
import requests
import pandas as pd
from datetime import datetime

from google.cloud import storage

def fetch_alpha_data(**kwargs):
    """
    Fetch data from Alpha Vantage for USO, AAPL, QQQ, plus AUD/CNY and USD/CNY.
    Save the results as CSV files into GCS under a 'raw' directory.
    """

    api_key = os.environ.get("ALPHA_VANTAGE_API_KEY")
    if not api_key:
        raise ValueError("Missing ALPHA_VANTAGE_API_KEY environment variable.")

    # symbols for equities/ETF and forex pairs
    symbols_equity = ["USO", "AAPL", "QQQ"]  # USO (Oil ETF), Apple, Nasdaq ETF
    # For forex pairs, we specify tuples of (from_symbol, to_symbol)
    symbols_fx = [
        ("AUD", "CNY"),  # Australian Dollar vs. Chinese Yuan
        ("USD", "CNY"),  # US Dollar vs. Chinese Yuan
    ]

    # Initialize GCS client 
    bucket_name = os.environ["DATA_LAKE_BUCKET"]
    gcs_client = storage.Client()
    bucket = gcs_client.bucket(bucket_name)

    # Instead of datetime.utcnow(), use Australia/Sydney local time
    ts_str = datetime.utcnow().strftime("%Y-%m-%d-%H-%M")
    # ...

    # 1) Fetch stock/ETF symbols (USO, AAPL, QQQ)
    for sym in symbols_equity:
        # Alpha Vantage stock intraday, 30min interval
        url = (f"https://www.alphavantage.co/query?"
               f"function=TIME_SERIES_INTRADAY"
               f"&symbol={sym}"
               f"&interval=30min"
               f"&apikey={api_key}"
               f"&outputsize=compact")

        resp = requests.get(url)
        data = resp.json()
        key = "Time Series (30min)"
        if key not in data:
            print(f"[WARN] {sym} no data or error: {data}")
            continue

        ts_data = data[key]
        rows = []
        for time_str, values in ts_data.items():
            rows.append({
                "symbol": sym,
                "timestamp": time_str,
                "open": values["1. open"],
                "high": values["2. high"],
                "low":  values["3. low"],
                "close":values["4. close"],
                "volume":values["5. volume"]
            })
        df = pd.DataFrame(rows).sort_values("timestamp")

        # Store CSV in GCS 
        file_path = f"raw/alpha_vantage/{sym}/{ts_str}.csv"
        blob = bucket.blob(file_path)
        blob.upload_from_string(df.to_csv(index=False), content_type="text/csv")
        print(f"[INFO] Uploaded {sym} -> {file_path}")

    # 2) Fetch forex pairs (AUD/CNY, USD/CNY)
    for from_sym, to_sym in symbols_fx:
        # Alpha Vantage: function=FX_INTRADAY, interval=30min
        url = (f"https://www.alphavantage.co/query?"
               f"function=CURRENCY_EXCHANGE_RATE"
               f"&from_currency={from_sym}"
               f"&to_currency={to_sym}"
               f"&interval=30min"
               f"&apikey={api_key}" )

        resp = requests.get(url)
        data = resp.json()
        key_fx = "Time Series FX (30min)"

        fx_key = "Realtime Currency Exchange Rate"
        if fx_key not in data:
            print(f"[WARN] {from_sym}/{to_sym} no real-time data: {data}")
            continue
        fx_info = data[fx_key]

        exchange_rate = fx_info.get("5. Exchange Rate")
        last_refreshed = fx_info.get("6. Last Refreshed")
        if not exchange_rate:
            print(f"[WARN] No '5. Exchange Rate' for {from_sym}/{to_sym}: {data}")
            continue

        rows = [{
            "symbol": f"{from_sym}/{to_sym}",
            "local_timestamp": ts_str,       
            "last_refreshed_utc": last_refreshed,
            "exchange_rate": exchange_rate
        }]
        df = pd.DataFrame(rows)

        sym_label = f"{from_sym}_{to_sym}"
        file_path = f"raw/alpha_vantage/{sym_label}/{ts_str}.csv"

        blob = bucket.blob(file_path)
        blob.upload_from_string(df.to_csv(index=False), content_type="text/csv")
        print(f"[INFO] Uploaded realtime {sym_label} -> {file_path}")
