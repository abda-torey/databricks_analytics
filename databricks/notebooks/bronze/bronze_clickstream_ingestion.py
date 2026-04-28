# databricks/notebooks/bronze/bronze_clickstream_ingestion.py
# Databricks notebook source

import sys
import json
sys.path.insert(0, "/Workspace/Repos/mega-ecommerce/src")

from pyspark.sql import functions as F
from pyspark.sql.types import StringType
from common.utils import get_logger, get_env_config, get_storage_path, get_table_name, get_databricks_secret, build_job_metadata

logger = get_logger("bronze.clickstream")

# ── Widget ────────────────────────────────────────────────────────────────────
dbutils.widgets.text("environment", "dev")
env = dbutils.widgets.get("environment")

cfg  = get_env_config(env)
meta = build_job_metadata(env, "bronze_clickstream_ingestion", "bronze")
logger.info(f"Starting bronze ingestion: {meta}")

# ── Paths and table names ─────────────────────────────────────────────────────
BRONZE_TABLE    = get_table_name(env, "bronze", "clickstream_raw")
BRONZE_PATH     = get_storage_path(env, "bronze", "clickstream")
CHECKPOINT_PATH = get_storage_path(env, "bronze", "_checkpoints/clickstream")

# ── Event Hub config ──────────────────────────────────────────────────────────
eh_conn_str = get_databricks_secret(dbutils, cfg["secret_scope"], "eventhub-consumer-connection-string")

eh_conf = {
    "eventhubs.connectionString": sc._jvm.org.apache.spark.eventhubs \
        .EventHubsUtils.encrypt(eh_conn_str),
    "eventhubs.consumerGroup": "$Default",
    "eventhubs.startingPosition": json.dumps({
        "offset": "-1", "seqNo": -1,
        "enqueuedTime": None, "isInclusive": True
    }),
}

# ── Read from Event Hubs ──────────────────────────────────────────────────────
logger.info("Connecting to Event Hubs...")
raw_stream = (
    spark.readStream
    .format("eventhubs")
    .options(**eh_conf)
    .load()
)

# ── Minimal transformation — bronze stays raw ─────────────────────────────────
bronze_stream = (
    raw_stream.select(
        F.col("body").cast(StringType()).alias("raw_payload"),
        F.col("enqueuedTime").alias("ingested_at"),
        F.col("partition").alias("partition_id"),
        F.col("offset"),
        F.col("sequenceNumber").alias("sequence_number"),
        F.lit(env).alias("environment"),
        F.current_timestamp().alias("processing_time"),
        F.to_date(F.col("enqueuedTime")).alias("event_date"),
    )
)

# ── Write to Delta (bronze layer) ─────────────────────────────────────────────
logger.info(f"Writing to {BRONZE_TABLE}")
query = (
    bronze_stream.writeStream
    .format("delta")
    .outputMode("append")
    .option("checkpointLocation", CHECKPOINT_PATH)
    .partitionBy("event_date")
    .trigger(processingTime="30 seconds")
    .toTable(BRONZE_TABLE)
)

logger.info("Bronze streaming query started")
query.awaitTermination()