import logging
import pandas as pd
from google.cloud import storage
from datetime import datetime

logger = logging.getLogger(__name__)

def upload_df_to_gcs(df: pd.DataFrame, bucket_name: str, prefix: str, file_format="csv"):
    """
    Uploads a DataFrame to GCS with a given prefix + timestamp filename.
    """
    if df.empty:
        logger.warning("DataFrame is empty, skipping upload.")
        return

    # Construct filename
    ts_str = datetime.utcnow().strftime("%Y-%m-%d-%H-%M")
    file_name = f"{prefix}/{ts_str}.{file_format}"

    client = storage.Client()  # assumes default credentials or env var
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(file_name)

    if file_format == "csv":
        content = df.to_csv(index=False)
        blob.upload_from_string(content, content_type="text/csv")
    else:
        # Could handle parquet, etc.
        pass

    logger.info(f"Uploaded DF to gs://{bucket_name}/{file_name}")

