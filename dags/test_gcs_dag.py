from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime

def list_buckets(**kwargs):
    from google.cloud import storage
    storage_client = storage.Client()
    buckets = list(storage_client.list_buckets())
    print("Found buckets:", buckets)

with DAG(
    "test_gcs_dag",
    start_date=datetime(2023,1,1),
    schedule_interval=None,
    catchup=False
) as dag:
    test_task = PythonOperator(
        task_id='list_buckets',
        python_callable=list_buckets,
    )
