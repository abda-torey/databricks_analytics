# Databricks notebook source

# COMMAND ----------

# MAGIC %md
# MAGIC # Gold — Clickstream KPIs
# MAGIC Reads cleaned Silver data and produces business-level aggregations.
# MAGIC
# MAGIC **Layer:** Gold (business aggregates)
# MAGIC **Mode:** Batch (run on schedule or manually)
# MAGIC **Input:** `dev_catalog.silver.clickstream_clean`
# MAGIC **Outputs:**
# MAGIC - `dev_catalog.gold.daily_ecommerce_kpis`
# MAGIC - `dev_catalog.gold.product_performance`

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 1: Imports

# COMMAND ----------

import sys

sys.path.insert(0, "/Workspace/Repos/mega-ecommerce/src")

from common.utils import (
    get_logger,
    get_env_config,
    get_table_name,
    build_job_metadata,
)
from common.transformers import (
    apply_gold_daily_kpis,
    apply_gold_product_performance,
)

logger = get_logger("gold.clickstream")
print("Imports successful")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 2: Widget — Set Environment

# COMMAND ----------

dbutils.widgets.text("environment", "dev")
env = dbutils.widgets.get("environment")

meta = build_job_metadata(env, "gold_clickstream_kpis", "gold")

logger.info(f"Starting gold aggregation: {meta}")
print(f"Environment : {env}")
print(f"Run time    : {meta['run_time']}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 3: Table Names

# COMMAND ----------

SILVER_TABLE = get_table_name(env, "silver", "clickstream_clean")
GOLD_DAILY   = get_table_name(env, "gold",   "daily_ecommerce_kpis")
GOLD_PRODUCT = get_table_name(env, "gold",   "product_performance")

print(f"Reading from : {SILVER_TABLE}")
print(f"Writing to   : {GOLD_DAILY}")
print(f"Writing to   : {GOLD_PRODUCT}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 4: Read Silver (Batch)
# MAGIC Gold runs as a batch job on a schedule — not streaming.

# COMMAND ----------

logger.info(f"Reading from {SILVER_TABLE}")

silver_df = spark.read.table(SILVER_TABLE)

print(f"Silver row count : {silver_df.count()}")
print(f"Silver columns   : {silver_df.columns}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 5: Apply Daily KPI Aggregation
# MAGIC Aggregation logic delegated to `apply_gold_daily_kpis()` from `src/common/transformers.py`.

# COMMAND ----------

daily_kpis = apply_gold_daily_kpis(silver_df)

print("Daily KPIs computed")
daily_kpis.show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 6: Apply Product Performance Aggregation

# COMMAND ----------

product_perf = apply_gold_product_performance(silver_df)

print("Product performance computed")
product_perf.show(5, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 7: Write Daily KPIs to Gold

# COMMAND ----------

logger.info(f"Writing daily KPIs to {GOLD_DAILY}")

(
    daily_kpis.write
    .format("delta")
    .mode("overwrite")
    .option("replaceWhere", "event_date >= current_date() - 7")
    .saveAsTable(GOLD_DAILY)
)

print(f"Daily KPIs written to {GOLD_DAILY}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 8: Write Product Performance to Gold

# COMMAND ----------

logger.info(f"Writing product performance to {GOLD_PRODUCT}")

(
    product_perf.write
    .format("delta")
    .mode("overwrite")
    .option("replaceWhere", "event_date >= current_date() - 7")
    .saveAsTable(GOLD_PRODUCT)
)

print(f"Product performance written to {GOLD_PRODUCT}")
logger.info("Gold tables updated successfully")

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 9: Verification — Preview Gold Tables

# COMMAND ----------

print("=== Daily Ecommerce KPIs ===")
spark.read.table(GOLD_DAILY).show(10, truncate=False)

print("=== Product Performance ===")
spark.read.table(GOLD_PRODUCT).show(10, truncate=False)

# COMMAND ----------

# MAGIC %md
# MAGIC ## Cell 10: Summary Statistics

# COMMAND ----------

from pyspark.sql import functions as F

daily = spark.read.table(GOLD_DAILY)
product = spark.read.table(GOLD_PRODUCT)

print("=== Daily KPI Summary ===")
daily.select(
    F.sum("total_revenue").alias("total_revenue_all_time"),
    F.sum("total_purchases").alias("total_purchases_all_time"),
    F.avg("conversion_rate").alias("avg_conversion_rate"),
    F.avg("cart_abandonment_rate").alias("avg_cart_abandonment"),
).show(truncate=False)

print("=== Top 5 Products by Revenue ===")
product.orderBy(F.col("revenue").desc()).show(5, truncate=False)