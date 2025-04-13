from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from datetime import datetime, timedelta
import os

from src.alpha_vantage_api import call_alpha_vantage
from src.ingest_stock import fetch_equities_data
from src.ingest_forex import fetch_forex_data
from src.upload_gcs import upload_df_to_gcs


def spark_transform(**kwargs):

    import subprocess
    cmd = [
        "spark-submit",
        "--master", "spark://spark-master:7077",
        "--jars", "/opt/spark/jars/gcs-connector-hadoop3-latest.jar",
        "/opt/airflow/src/transform_data.py"
    ]
    try:
        # Capture logs from stdout / stderr
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
    except subprocess.CalledProcessError as e:
        # Print them in Airflow logs, so you can see the real error
        print("----- STDOUT -----")
        print(e.stdout.decode(errors="replace"))
        print("----- STDERR -----")
        print(e.stderr.decode(errors="replace"))
        raise

def dbt_run(**kwargs):
    import subprocess
    cmd = [
        "dbt", "run",
        "--profiles-dir", "/opt/airflow/dbt",  
        "--project-dir", "/opt/airflow/dbt"
    ]
    try:
        proc = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("DBT STDOUT:", proc.stdout.decode("utf-8", errors="replace"))
    except subprocess.CalledProcessError as e:
        # Print both stdout/stderr so we see the real error message
        print("----- DBT STDOUT -----")
        print(e.stdout.decode("utf-8", errors="replace"))
        print("----- DBT STDERR -----")
        print(e.stderr.decode("utf-8", errors="replace"))
        raise


def do_analysis(**kwargs):
    """
    An example analysis step: run a BigQuery query or some Python logic.
    """
    from google.cloud import bigquery
    project_id = os.environ["GCP_PROJECT_ID"] 
    dataset_id = os.environ["GCP_DATASET_ID"]


    bq_client = bigquery.Client()

    # 1) Stocks
    stocks_query = f"""
    SELECT 
      symbol, 
      AVG(close) AS avg_close
    FROM `{project_id}.{dataset_id}.final_table_stocks`
    GROUP BY symbol
    """
    stock_rows = bq_client.query(stocks_query).result()
    print("[INFO] Average close by stock symbol:")
    for row in stock_rows:
        print(f"Symbol={row.symbol},  AvgClose={row.avg_close}")

    # 2) Forex
    forex_query = f"""
    SELECT 
      symbol, 
      AVG(exchange_rate) AS avg_fx
    FROM `{project_id}.{dataset_id}.final_table_forex`
    GROUP BY symbol
    """
    forex_rows = bq_client.query(forex_query).result()
    print("\n[INFO] Average exchange rate by forex symbol:")
    for row in forex_rows:
        print(f"Symbol={row.symbol},  AvgFX={row.avg_fx}")


# ----------------------------------------
#  Airflow DAG 
# ----------------------------------------

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023,1,1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    dag_id="alpha_vantage_pipeline",
    schedule_interval="0 8,12,16,20 * * *",
    default_args=default_args,
    catchup=False
)

# 1) Ingestion stocks
def ingest_stocks(**kwargs):

    df_stocks = fetch_equities_data(
        api_key=os.environ["ALPHA_VANTAGE_API_KEY"],
        symbols=["AAPL", "QQQ", "USO"], 
        interval="30min",
        outputsize="full"             
    )
    kwargs['ti'].xcom_push(key='stocks_df', value=df_stocks.to_json())

ingest_stocks_task = PythonOperator(
    task_id="ingest_stocks",
    python_callable=ingest_stocks,
    provide_context=True,
    dag=dag
)


#  2) Ingestion Forex
def ingest_fx(**kwargs):
    df_forex = fetch_forex_data(
        api_key=os.environ["ALPHA_VANTAGE_API_KEY"],
        fx_pairs=["AUD/CNY", "USD/CNY"], 
        outputsize="full"
    )
    kwargs['ti'].xcom_push(key='forex_df', value=df_forex.to_json())

ingest_fx_task = PythonOperator(
    task_id="ingest_fx",
    python_callable=ingest_fx,
    provide_context=True,
    dag=dag
)


# 3) upload stocks
def upload_stocks(**kwargs):
    import pandas as pd
    df_json = kwargs['ti'].xcom_pull(task_ids='ingest_stocks', key='stocks_df')
    if df_json:
        df = pd.read_json(df_json)

        upload_df_to_gcs(df, bucket_name=os.environ["DATA_LAKE_BUCKET"], 
                         prefix="raw/alpha_vantage", 
                         file_format="csv")

upload_stocks_task = PythonOperator(
    task_id="upload_stocks",
    python_callable=upload_stocks,
    provide_context=True,
    dag=dag
)


#  4) Upload forex
def upload_fx(**kwargs):
    import pandas as pd
    df_json = kwargs['ti'].xcom_pull(task_ids='ingest_fx', key='forex_df')
    if df_json:
        df = pd.read_json(df_json)
        from src.upload_gcs import upload_df_to_gcs
        upload_df_to_gcs(df, bucket_name=os.environ["DATA_LAKE_BUCKET"], 
                         prefix="raw/alpha_vantage", 
                         file_format="csv")

upload_fx_task = PythonOperator(
    task_id="upload_fx",
    python_callable=upload_fx,
    provide_context=True,
    dag=dag
)



# 5) Spark transformation
spark_task = PythonOperator(
    task_id="spark_transform",
    python_callable=spark_transform,
    dag=dag
)


   
# 6) Load to BigQuery

load_transformed_data = GCSToBigQueryOperator(
    task_id='load_transformed_data',
    bucket=os.environ["DATA_LAKE_BUCKET"],
    source_objects=['transformed_data/*.parquet'],
    destination_project_dataset_table=f"{os.environ['GCP_PROJECT_ID']}.{os.environ['GCP_DATASET_ID']}.bigquery_data",
    source_format='PARQUET',
    write_disposition='WRITE_APPEND',
    dag=dag
)



# 7) dbt run
dbt_task = PythonOperator(
    task_id="dbt_run",
    python_callable=dbt_run,
    dag=dag
)

# 8) Analysis / final query
analysis_task = PythonOperator(
    task_id='analysis_task',
    python_callable=do_analysis,
    dag=dag
)

# Task Dependencies
ingest_stocks_task >> upload_stocks_task
ingest_fx_task >> upload_fx_task

[upload_stocks_task, upload_fx_task] >> spark_task

spark_task >> load_transformed_data >> dbt_task >> analysis_task
