import pandas as pd
import logging
from .alpha_vantage_api import call_alpha_vantage

logger = logging.getLogger(__name__)

def fetch_equities_data(api_key: str, symbols: list, interval: str = "30min", outputsize: str=None):
    """
    Calls the Alpha Vantage TIME_SERIES_INTRADAY for multiple stock symbols,
    merges results into a single DataFrame.
    """
    all_dfs = []
    for sym in symbols:
        df = call_alpha_vantage(api_key=api_key,
                                function="TIME_SERIES_INTRADAY",
                                symbol=sym,
                                interval=interval,
                                outputsize=outputsize
                              )
        if not df.empty:
            all_dfs.append(df)

    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        logger.info(f"Fetched equities data for {len(symbols)} symbols, rows={len(final_df)}")
        return final_df
    else:
        logger.warning("No equity data fetched.")
        return pd.DataFrame()

