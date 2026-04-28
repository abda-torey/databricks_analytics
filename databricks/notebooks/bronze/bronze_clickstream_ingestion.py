# Databricks notebook source

# COMMAND ----------

# MAGIC %md
# MAGIC # Bronze — Clickstream Ingestion
# MAGIC Reads raw events from Azure Event Hubs and writes to Delta table.
# MAGIC
# MAGIC **Layer:** Bronze (raw, no transformation)
# MAGIC **Trigger:** 30 second micro-batch
# MAGIC **Output:** `dev_catalog.bronze.clickstream_raw`

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 1: Imports

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

# Now import from src/
from common.utils import (
    get_logger, get_env_config, get_storage_path,
    get_table_name, get_databricks_secret, build_job_metadata,
)

print("Imports successful")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 2: Widget — Set Environment

# COMMAND ----------

dbutils.widgets.text("environment", "dev")
env = dbutils.widgets.get("environment")

cfg  = get_env_config(env)
meta = build_job_metadata(env, "bronze_clickstream_ingestion", "bronze")

logger.info(f"Starting bronze ingestion: {meta}")
print(f"Environment : {env}")
print(f"Catalog     : {cfg['catalog']}")
print(f"Storage     : {cfg['storage_account']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 3: Paths and Table Names

# COMMAND ----------

BRONZE_TABLE    = get_table_name(env, "bronze", "clickstream_raw")
BRONZE_PATH     = get_storage_path(env, "bronze", "clickstream")
CHECKPOINT_PATH = get_storage_path(env, "bronze", "_checkpoints/clickstream")

print(f"Bronze table    : {BRONZE_TABLE}")
print(f"Bronze path     : {BRONZE_PATH}")
print(f"Checkpoint path : {CHECKPOINT_PATH}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 4: Event Hub Configuration

# COMMAND ----------

eh_conn_str = get_databricks_secret(
    dbutils,
    cfg["secret_scope"],
    "eventhub-consumer-connection-string"
)

eh_conf = {
    "eventhubs.connectionString": sc._jvm.org.apache.spark.eventhubs \
        .EventHubsUtils.encrypt(eh_conn_str),
    "eventhubs.consumerGroup": "$Default",
    "eventhubs.startingPosition": json.dumps({
        "offset": "-1",
        "seqNo": -1,
        "enqueuedTime": None,
        "isInclusive": True
    }),
}

print("Event Hub config ready")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 5: Read from Event Hubs (Streaming)

# COMMAND ----------

logger.info("Connecting to Event Hubs...")

raw_stream = (
    spark.readStream
    .format("eventhubs")
    .options(**eh_conf)
    .load()
)

print("Stream reader created")
print(f"Schema: {raw_stream.schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 6: Select and Rename Columns
# MAGIC Bronze stays raw — no parsing, no cleaning. Just rename columns for clarity.

# COMMAND ----------

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

print("Bronze stream transformation defined")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 7: Write to Delta (Start Streaming Query)
# MAGIC
# MAGIC This cell starts the streaming query. It will run continuously.
# MAGIC **Stop the stream** by clicking the stop button or interrupting the cluster.

# COMMAND ----------

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

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 8: Verification
# MAGIC Run this cell **in a separate notebook** while the stream above is running.
# MAGIC Do not run it in this notebook — it will not execute while awaitTermination() is blocking.

# COMMAND ----------

# Run this in a separate notebook to verify data is flowing:
#
# df = spark.read.table("dev_catalog.bronze.clickstream_raw")
# print(f"Row count: {df.count()}")
# df.show(5, truncate=False)