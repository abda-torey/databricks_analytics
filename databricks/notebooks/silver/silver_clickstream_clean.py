# databricks/notebooks/silver/silver_clickstream_clean.py
# Databricks notebook source

import sys
sys.path.insert(0, "/Workspace/Repos/mega-ecommerce/src")

from pyspark.sql import functions as F
from pyspark.sql.types import *
from common.utils import get_logger, get_env_config, get_storage_path, get_table_name, build_job_metadata
from common.transformers import apply_silver_cleaning

logger = get_logger("silver.clickstream")

# ── Widget ────────────────────────────────────────────────────────────────────
dbutils.widgets.text("environment", "dev")
env = dbutils.widgets.get("environment")

cfg  = get_env_config(env)
meta = build_job_metadata(env, "silver_clickstream_clean", "silver")
logger.info(f"Starting silver cleaning: {meta}")

# ── Tables and paths ──────────────────────────────────────────────────────────
BRONZE_TABLE    = get_table_name(env, "bronze", "clickstream_raw")
SILVER_TABLE    = get_table_name(env, "silver", "clickstream_clean")
CHECKPOINT_PATH = get_storage_path(env, "silver", "_checkpoints/clickstream_clean")

# ── Schema for parsing raw JSON payload ───────────────────────────────────────
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

# ── Read Bronze ───────────────────────────────────────────────────────────────
logger.info(f"Reading from {BRONZE_TABLE}")
bronze_stream = spark.readStream.format("delta").table(BRONZE_TABLE)

# ── Parse JSON then apply shared cleaning logic from src/ ─────────────────────
parsed_stream = (
    bronze_stream
    .withColumn("parsed", F.from_json(F.col("raw_payload"), clickstream_schema))
    .select("parsed.*", "ingested_at", "processing_time")
)

silver_stream = apply_silver_cleaning(parsed_stream)  # from src/common/transformers.py

# ── Write to Silver ───────────────────────────────────────────────────────────
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