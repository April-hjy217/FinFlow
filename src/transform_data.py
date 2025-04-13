from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, lit, current_timestamp


def main():
    spark = SparkSession.builder.appName("AlphaVantageSparkTransform").getOrCreate()

    # Read raw CSV files from GCS
    df_all = spark.read.option("header", True).csv("gs://finflow-455108-data-lake/raw/alpha_vantage/*/*.csv")

    numeric_columns = ["open", "high", "low", "close", "volume"]
    for col_name in numeric_columns:
        dtype = "long" if col_name == "volume" else "double"
        df_all = df_all.withColumn(col_name, col(col_name).cast(dtype))

    # Add a column to distinguish forex vs equity
    df_all = df_all.withColumn(
        "data_type",
        when(col("symbol").contains("/"), lit("forex")).otherwise(lit("equity"))
    )

    # Add ingestion timestamp
    df_all = df_all.withColumn("ingestion_time", current_timestamp())

    # Write to GCS with partitioning on ingestion_time
    df_all.write.partitionBy("ingestion_time").mode("overwrite").parquet("gs://finflow-455108-data-lake/transformed_data/")


    spark.stop()

if __name__ == "__main__":
    main()