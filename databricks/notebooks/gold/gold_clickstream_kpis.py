# databricks/notebooks/gold/gold_clickstream_kpis.py
# Databricks notebook source

import sys
sys.path.insert(0, "/Workspace/Repos/mega-ecommerce/src")

from common.utils import get_logger, get_env_config, get_table_name, build_job_metadata
from common.transformers import apply_gold_daily_kpis, apply_gold_product_performance

logger = get_logger("gold.clickstream")

# ── Widget ────────────────────────────────────────────────────────────────────
dbutils.widgets.text("environment", "dev")
env = dbutils.widgets.get("environment")

meta = build_job_metadata(env, "gold_clickstream_kpis", "gold")
logger.info(f"Starting gold aggregation: {meta}")

# ── Tables ────────────────────────────────────────────────────────────────────
SILVER_TABLE  = get_table_name(env, "silver", "clickstream_clean")
GOLD_DAILY    = get_table_name(env, "gold",   "daily_ecommerce_kpis")
GOLD_PRODUCT  = get_table_name(env, "gold",   "product_performance")

# ── Read Silver (batch — gold runs on a schedule) ────────────────────────────
logger.info(f"Reading from {SILVER_TABLE}")
silver_df = spark.read.table(SILVER_TABLE)

# ── Apply aggregations from src/ ──────────────────────────────────────────────
daily_kpis   = apply_gold_daily_kpis(silver_df)
product_perf = apply_gold_product_performance(silver_df)

# ── Write Gold tables ─────────────────────────────────────────────────────────
logger.info(f"Writing daily KPIs to {GOLD_DAILY}")
(
    daily_kpis.write
    .format("delta")
    .mode("overwrite")
    .option("replaceWhere", "event_date >= current_date() - 7")
    .saveAsTable(GOLD_DAILY)
)

logger.info(f"Writing product performance to {GOLD_PRODUCT}")
(
    product_perf.write
    .format("delta")
    .mode("overwrite")
    .option("replaceWhere", "event_date >= current_date() - 7")
    .saveAsTable(GOLD_PRODUCT)
)

logger.info("Gold tables updated successfully")