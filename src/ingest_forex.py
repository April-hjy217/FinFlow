import pandas as pd
import logging
from .alpha_vantage_api import call_alpha_vantage

logger = logging.getLogger(__name__)

def fetch_forex_data(api_key: str, fx_pairs: list, outputsize: str=None):
    """
    Calls the Alpha Vantage FX_INTRADAY (or FX_DAILY, etc.) for multiple forex pairs,
    merges results into a single DataFrame.
    """
    all_dfs = []
    for pair in fx_pairs:
        df = call_alpha_vantage(
            api_key=api_key,
            function="FX_DAILY", 
            symbol=pair,
            outputsize=outputsize
        )
        if not df.empty:
            all_dfs.append(df)

    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        logger.info(f"Fetched forex data (daily) for {len(fx_pairs)} pairs, rows={len(final_df)}")
        return final_df
    else:
        logger.warning("No daily forex data fetched.")
        return pd.DataFrame()
