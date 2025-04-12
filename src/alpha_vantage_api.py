import requests
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def call_alpha_vantage(api_key: str, function: str, symbol: str, interval: str = None, outputsize: str = None):
    """
    Makes a request to Alpha Vantage for a given symbol and function.
    Automatically handles both stock (TIME_SERIES_xxx) and FX (FX_xxx) data.
    :param api_key: Alpha Vantage API key
    :param function: e.g. "TIME_SERIES_INTRADAY", "TIME_SERIES_DAILY", "FX_INTRADAY", "FX_DAILY", etc.
    :param symbol: for stocks: e.g. "AAPL"; for FX: "AUD/CNY" 
    :param interval: e.g. '30min', '15min', etc
    :param outputsize: "full" or "compact"
    :return: A DataFrame with columns like 'timestamp', 'open', 'high', 'low', 'close', etc.
    """
    base_url = "https://www.alphavantage.co/query?"

    # Basic request parameters
    params = {
        "apikey": api_key,
        "function": function,
    }
   
    # If it's an FX function (e.g. "FX_INTRADAY"), split the symbol into from_symbol and to_symbol
    if function.startswith("FX_"):
        from_sym, to_sym = symbol.split("/")
        params["from_symbol"] = from_sym
        params["to_symbol"] = to_sym
    else:
        # Otherwise, treat it as a stock symbol
        params["symbol"] = symbol

    # If it's intraday (e.g. TIME_SERIES_INTRADAY or FX_INTRADAY) and we have an interval, add it
    if function.endswith("_INTRADAY") and interval:
        params["interval"] = interval

    # If outputsize is specified, add it to params
    if outputsize:
        params["outputsize"] = outputsize

    logger.info(f"[API] Requesting {function} for {symbol} with interval={interval}")
    resp = requests.get(base_url, params=params)
    data = resp.json()

    # Choose the right data key based on whether it's FX or stock, and intraday vs. daily
    if function.startswith("FX_"):
        if interval:
            data_key = f"Time Series FX ({interval})"
        else:
            # If no interval is specified for FX, assume Daily (could also choose Weekly or Monthly)
            data_key = "Time Series FX (Daily)"
    else:
        # Stock data
        if interval:
            data_key = f"Time Series ({interval})"
        else:
            data_key = "Time Series (Daily)"

    # If the expected data key isn't in the JSON, return an empty DataFrame
    if data_key not in data:
        logger.warning(f"No data found in response for {symbol}: {data}")
        return pd.DataFrame()

    # Parse the time-series data into a list of rows
    ts_data = data[data_key]
    rows = []
    for time_str, values in ts_data.items():
        rows.append({
            "timestamp": time_str,
            "open": values.get("1. open"),
            "high": values.get("2. high"),
            "low": values.get("3. low"),
            "close": values.get("4. close"),
            "volume": values.get("5. volume"),
        })

    # Convert the rows into a DataFrame and add a 'symbol' column
    df = pd.DataFrame(rows)
    df["symbol"] = symbol
    return df