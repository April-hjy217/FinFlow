from pyspark.sql import SparkSession
from pyspark.sql.functions import col, when, lit

def main():
    spark = SparkSession.builder.appName("AlphaVantageSparkTransform").getOrCreate()

    df_all = spark.read.option("header", True).csv("gs://finflow-455108-data-lake/raw/alpha_vantage/*/*.csv")


    df_all = df_all.withColumn("open", col("open").cast("double"))
    df_all = df_all.withColumn("volume", col("volume").cast("long"))

    df_all = df_all.withColumn(
        "data_type",
        when(col("symbol").contains("/"), lit("forex")).otherwise(lit("equity"))
    )


    df_all.write.mode("overwrite").parquet("gs://finflow-455108-data-lake/transformed_data/")

    spark.stop()

if __name__ == "__main__":
    main()
