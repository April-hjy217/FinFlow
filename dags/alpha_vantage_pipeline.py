from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.google.cloud.transfers.gcs_to_bigquery import GCSToBigQueryOperator
from datetime import datetime, timedelta
import os
# from airflow.operators.short_circuit import ShortCircuitOperator
from scripts.alpha_vantage_ingestion import fetch_alpha_data

def spark_transform(**kwargs):

    import subprocess
    cmd = [
        "spark-submit",
        "--master", "spark://spark-master:7077",
        "/opt/airflow/scripts/transform_data.py"
    ]
    subprocess.run(cmd, check=True)

def dbt_run(**kwargs):
    import subprocess
    cmd = [
        "dbt", "run",
        "--profiles-dir", "/opt/airflow/dbt",  
        "--project-dir", "/opt/airflow/dbt"
    ]
    subprocess.run(cmd, check=True)


def do_analysis(**kwargs):
    """
    An example analysis step: run a BigQuery query or some Python logic.
    """
    from google.cloud import bigquery
    project_id = os.environ["GCP_PROJECT_ID"] 
    dataset_id = os.environ["GCP_DATASET_ID"]


    bq_client = bigquery.Client()

    # 1) Stocks Table
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

    # 2) Forex Table
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

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2023,1,1),
    'retries': 1,
    'retry_delay': timedelta(minutes=5)
}

dag = DAG(
    dag_id="alpha_vantage_pipeline",
    # 4 times a day at 08:00, 12:00, 16:00, 20:00
    schedule_interval="0 8,12,16,20 * * *",
    default_args=default_args,
    catchup=False
)

# 1) Ingestion task
ingestion_task = PythonOperator(
    task_id="ingest_alpha_data",
    python_callable=fetch_alpha_data,
    dag=dag
)

# 2) Spark transformation
spark_task = PythonOperator(
    task_id="spark_transform",
    python_callable=spark_transform,
    dag=dag
)


# 3) dbt run
dbt_task = PythonOperator(
    task_id="dbt_run",
    python_callable=dbt_run,
    dag=dag
)



# # 4)check_forex_files
# check_forex_files = ShortCircuitOperator(
#     task_id='check_forex_files',
#     python_callable=check_gcs_forex,
#     dag=dag
# )




project_id = os.environ["GCP_PROJECT_ID"]     
dataset_id = os.environ["GCP_DATASET_ID"]   
# 4) Load to BigQuery
load_stocks = GCSToBigQueryOperator(
    task_id='load_stocks',
    bucket = os.environ["DATA_LAKE_BUCKET"],
    source_objects=['raw/alpha_vantage/USO/*.csv', 'raw/alpha_vantage/AAPL/*.csv', 'raw/alpha_vantage/QQQ/*.csv'],
    destination_project_dataset_table=f"{project_id}.{dataset_id}.final_table_stocks",
    source_format='CSV',
    autodetect=True,
    write_disposition='WRITE_TRUNCATE',
    dag=dag
)

load_forex = GCSToBigQueryOperator(
    task_id='load_forex',
    bucket = os.environ["DATA_LAKE_BUCKET"],
    source_objects=['raw/alpha_vantage/AUD_CNY/*.csv', 'raw/alpha_vantage/USD_CNY/*.csv'],
    destination_project_dataset_table=f"{project_id}.{dataset_id}.final_table_forex",
    source_format='CSV',
    autodetect=True,
    write_disposition='WRITE_APPEND',
    dag=dag
)

# 5) Analysis / final query
analysis_task = PythonOperator(
    task_id='analysis_task',
    python_callable=do_analysis,
    dag=dag
)

# Define task dependencies in a chain
# ingestion_task >> spark_task >> dbt_task
# dbt_task >> load_stocks >> analysis_task
# dbt_task >> check_forex_files >> load_forex >> analysis_task

ingestion_task >> spark_task >> dbt_task >> [load_stocks, load_forex] >> analysis_task
