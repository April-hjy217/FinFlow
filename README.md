# FinFlow Data Pipeline

A data engineering project using **Alpha Vantage** APIs, **Airflow**, **Spark**, **dbt**, and **BigQuery** to ingest, transform, and analyze financial data—such as **Forex** (AUD/CNY, USD/CNY) and **stocks** (AAPL, QQQ, USO). This pipeline stores raw data in GCS, processes it via Spark/dbt, and loads deduplicated, final tables into BigQuery for analytics. A **Metabase** or **Looker Studio** dashboard can then visualize insights.

---

## Final Dashboard

- **Link**: [Metabase Dashboard](https://glorious-broccoli-x5pv7rg9gp4g3vxq4-3000.app.github.dev/public/dashboard/c0e448a2-17d9-475e-b92b-ab8a1d0c0de5)

---

## 1. Problem Description

Recent fluctuations in both **stock** and **foreign exchange** rates (especially the **AUD/CNY** pair) often leave **me** guessing if it’s truly the right time to make a move. Relying on real-time banking exchange quotes alone can be frustrating, as it’s not easy to see longer trends or historical lows.

Hence, this project aims to build a **scalable pipeline** that:

1. **Schedules and Orchestrates** the workflow with **Airflow**.
2. **Extracts** data from **Alpha Vantage**.
3. **Stores** raw CSVs in **Google Cloud Storage (GCS)**.
4. **Transforms** them using **Spark** (batch processing) and **dbt** (for final cleaning/deduplication).
5. **Loads** final tables into **BigQuery**.
6. **Visualizes** the results in **Metabase** for insights on currency movements (AUD/CNY, USD/CNY) and stock/ETF performance (USO, AAPL, QQQ).

---

## 2. Project Structure

```
graphql
CopyEdit
FinFlow
├── credentials/                # *EXCLUDED from GitHub (contains key.json)
├── dags/
│   ├── alpha_vantage_pipeline.py   # Airflow DAG for ingestion + transformations
│   └── test_gcs_dag.py             # DAG for testing GCS
├── dbt/
│   ├── dbt_project.yml
│   ├── profiles.yml
│   ├── models/
│   │   ├── dedup_forex.sql
│   │   ├── dedup_stocks.sql
│   ├── sources.yml                # references final_table_forex, final_table_stocks
│   └── target/
├── docker/                       # .env is also ignored
│   ├── docker-compose.yml         # defines Postgres, pgAdmin, Airflow, Spark, Metabase
│   ├── Dockerfile_airflow         # Dockerfile for custom Airflow image
├── logs/                          # Airflow logs or custom logging
├── scripts/
│   ├── alpha_vantage_ingestion.py # Python script to fetch data from Alpha Vantage
│   ├── transform_data.py          # might use it later
├── terraform/
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
├── .gitignore
├── README.md                      # instructions & overview
└── requirements.txt              # Python dependencies

```

---

## 3. Airflow ETL Pipeline

**`alpha_vantage_pipeline.py`** is the main DAG, which orchestrates these tasks:

```python
python
CopyEdit
ingestion_task = PythonOperator(
    task_id="ingest_alpha_data",
    python_callable=fetch_alpha_data,  # calls alpha_vantage_ingestion.py
)

spark_task = PythonOperator(
    task_id="spark_transform",
    python_callable=spark_transform,   # calls transform_data.py
)

dbt_task = PythonOperator(
    task_id="dbt_run",
    python_callable=dbt_run,
)

load_task_stocks = GCSToBigQueryOperator(...)
load_task_forex  = GCSToBigQueryOperator(...)

analysis_task = PythonOperator(
    task_id='analysis_task',
    python_callable=do_analysis,
)

ingestion_task >> spark_task >> dbt_task >> [load_task_stocks, load_task_forex] >> analysis_task

```
---

## 4. dbt Deduplication Models

- **`dedup_stocks.sql`**
- **`dedup_forex.sql`**

These read from final tables and produce **`final_table_stocks_clean`** / **`final_table_forex_clean`** with duplicates removed.

---

## 5. Deployment & Execution

### Prerequisites

- **Docker Compose** installed locally.
- A **GCP Project** with a **BigQuery** dataset & GCS bucket.
- **Alpha Vantage** API key for real data.

### Steps

1. **Clone** the repo:
    
    ```bash

    git clone https://github.com/.../finflow.git
    cd finflow
    
    ```
    
2. **Create** an `.env` file, filling in real values:
    
    ```
    ALPHA_VANTAGE_API_KEY=YOUR_REAL_KEY
    GCP_PROJECT_ID=your-project
    GCP_DATASET_ID=my_dataset
    DATA_LAKE_BUCKET=your-gcs-bucket
    
    ```
    
3. **Place** your real service account `key.json` in `credentials/`.
4. **Build & Run** containers:
    
    ```bash
    cd docker
    docker-compose build
    docker-compose up -d
    
    ```
    

### Airflow

- Go to [http://localhost:8080](http://localhost:8080/) (user: `admin`, pass: `admin`).
- Turn on `alpha_vantage_pipeline`.

---

## 6. Viewing Dashboards (Metabase)

- **URL**: [http://localhost:3000](http://localhost:3000/)
- Connect Metabase to BigQuery → see `final_table_stocks_clean` and `final_table_forex_clean`.

---


