# Databricks notebook source

# COMMAND ----------

# MAGIC %md
# MAGIC # Silver — Clickstream Cleaning
# MAGIC Reads raw JSON from Bronze, parses and cleans it, writes to Silver Delta table.
# MAGIC
# MAGIC **Layer:** Silver (parsed, cleaned, enriched)
# MAGIC **Trigger:** 60 second micro-batch
# MAGIC **Input:** `dev_catalog.bronze.clickstream_raw`
# MAGIC **Output:** `dev_catalog.silver.clickstream_clean`

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 1: Imports and Path Setup

# COMMAND ----------

import sys
import os

# Dynamic path — works regardless of GitHub username
notebook_path = dbutils.notebook.entry_point.getDbutils() \
    .notebook().getContext().notebookPath().get()
repo_root = "/Workspace" + "/".join(notebook_path.split("/")[:4])
src_path  = repo_root + "/src"
sys.path.insert(0, src_path)

print(f"Repo root : {repo_root}")
print(f"src path  : {src_path}")

from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField,
    StringType, DoubleType, IntegerType
)
from common.utils import (
    get_logger,
    get_env_config,
    get_storage_path,
    get_table_name,
    build_job_metadata,
)
from common.transformers import apply_silver_cleaning

print("Imports successful")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 2: Logger

# COMMAND ----------

logger = get_logger("silver.clickstream")
print("Logger ready")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 3: Widget — Set Environment

# COMMAND ----------

dbutils.widgets.text("environment", "dev")
env = dbutils.widgets.get("environment")

cfg  = get_env_config(env)
meta = build_job_metadata(env, "silver_clickstream_clean", "silver")

logger.info(f"Starting silver cleaning: {meta}")
print(f"Environment : {env}")
print(f"Catalog     : {cfg['catalog']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 4: Tables and Paths

# COMMAND ----------

BRONZE_TABLE    = get_table_name(env, "bronze", "clickstream_raw")
SILVER_TABLE    = get_table_name(env, "silver", "clickstream_clean")
CHECKPOINT_PATH = get_storage_path(env, "silver", "_checkpoints/clickstream_clean")

print(f"Reading from : {BRONZE_TABLE}")
print(f"Writing to   : {SILVER_TABLE}")
print(f"Checkpoint   : {CHECKPOINT_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 5: JSON Schema Definition
# MAGIC Explicit schema for parsing the raw_payload JSON field from Bronze.
# MAGIC Schema-on-read — Bronze stored it as a raw string.

# COMMAND ----------

clickstream_schema = StructType([
    StructField("event_id",         StringType(),  True),
    StructField("event_type",       StringType(),  True),
    StructField("event_timestamp",  StringType(),  True),
    StructField("session_id",       StringType(),  True),
    StructField("user_id",          StringType(),  True),
    StructField("anonymous_id",     StringType(),  True),
    StructField("page_url",         StringType(),  True),
    StructField("referrer_url",     StringType(),  True),
    StructField("device_type",      StringType(),  True),
    StructField("browser",          StringType(),  True),
    StructField("os",               StringType(),  True),
    StructField("country",          StringType(),  True),
    StructField("city",             StringType(),  True),
    StructField("product_id",       StringType(),  True),
    StructField("product_name",     StringType(),  True),
    StructField("product_category", StringType(),  True),
    StructField("product_price",    DoubleType(),  True),
    StructField("quantity",         IntegerType(), True),
    StructField("search_query",     StringType(),  True),
    StructField("revenue",          DoubleType(),  True),
])

print(f"Schema defined with {len(clickstream_schema.fields)} fields")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 6: Read Bronze (Streaming)

# COMMAND ----------

logger.info(f"Reading from {BRONZE_TABLE}")

bronze_stream = (
    spark.readStream
    .format("delta")
    .table(BRONZE_TABLE)
)

print("Bronze stream reader created")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 7: Parse JSON and Apply Cleaning
# MAGIC
# MAGIC Parsing happens here. Cleaning logic is delegated to `apply_silver_cleaning()`
# MAGIC from `src/common/transformers.py` — keeping this notebook thin and testable.

# COMMAND ----------

parsed_stream = (
    bronze_stream
    .withColumn("parsed", F.from_json(F.col("raw_payload"), clickstream_schema))
    .select("parsed.*", "ingested_at", "processing_time")
)

silver_stream = apply_silver_cleaning(parsed_stream)

print("Parsing and cleaning transformations defined")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 8: Write to Silver (Start Streaming Query)
# MAGIC
# MAGIC This cell starts the streaming query. It will run continuously.
# MAGIC **Stop the stream** by clicking the stop button or interrupting the cluster.

# COMMAND ----------

logger.info(f"Writing to {SILVER_TABLE}")

query = (
    silver_stream.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", CHECKPOINT_PATH)
    .partitionBy("event_date")
    .trigger(processingTime="60 seconds")
    .toTable(SILVER_TABLE)
)

logger.info("Silver streaming query started")
query.awaitTermination()

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 9: Verification
# MAGIC Run this in a **separate notebook** while the stream above is running.

# COMMAND ----------

# Run this in a separate notebook:
#
# df = spark.read.table("dev_catalog.silver.clickstream_clean")
# print(f"Row count: {df.count()}")
# print(f"Columns: {df.columns}")
# df.show(5, truncate=False)
#
# # Check null counts on critical fields
# from pyspark.sql import functions as F
# df.select([F.count(F.when(F.col(c).isNull(), c)).alias(c) for c in df.columns]).show()