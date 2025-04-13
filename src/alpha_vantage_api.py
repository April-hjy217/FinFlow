import requests
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def call_alpha_vantage(api_key, function, symbol, interval=None, outputsize=None):
    params = {
        "function": function,
        "apikey": api_key,
        "outputsize": outputsize,
        "interval": interval
    }


    # Add symbol parameters based on function type
    if function.startswith("FX_"):
        from_sym, to_sym = symbol.split("/")
        params.update({"from_symbol": from_sym, "to_symbol": to_sym})
    else:
        params["symbol"] = symbol

    # Remove any None values
    params = {k: v for k, v in params.items() if v is not None}

    # Make the API request
    response = requests.get("https://www.alphavantage.co/query", params=params)
    data = response.json()

    # Determine the correct data key
    prefix = "Time Series FX" if function.startswith("FX_") else "Time Series"
    suffix = f"({interval})" if interval else "(Daily)"
    data_key = f"{prefix} {suffix}"

    # If the expected data is missing, return empty DataFrame
    if data_key not in data:
        return pd.DataFrame()

    # Parse time series into a DataFrame
    df = pd.DataFrame([
        {
            "timestamp": t,
            "open": v.get("1. open"),
            "high": v.get("2. high"),
            "low": v.get("3. low"),
            "close": v.get("4. close"),
            "volume": v.get("5. volume")
        }
        for t, v in data[data_key].items()
    ])
    df["symbol"] = symbol
    return df

