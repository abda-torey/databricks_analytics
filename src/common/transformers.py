# src/common/transformers.py
"""
Pure Python and PySpark transformation functions.
Pure Python functions at the top — testable without a cluster.
PySpark DataFrame functions below — tested as integration tests on a cluster.
"""

import re
from typing import Optional
from datetime import datetime


# ── Pure Python (unit testable in CI without Spark) ───────────────────────────

def sanitise_string(value: Optional[str]) -> Optional[str]:
    """
    Strips whitespace and lowercases.
    Returns None if empty after stripping.

    >>> sanitise_string("  Chrome  ")
    'chrome'
    >>> sanitise_string("") is None
    True
    """
    if value is None:
        return None
    cleaned = value.strip().lower()
    return cleaned if cleaned else None


def sanitise_country_code(value: Optional[str]) -> Optional[str]:
    """
    Validates and uppercases a 2-letter ISO country code.
    Returns None if invalid.

    >>> sanitise_country_code("gb")
    'GB'
    >>> sanitise_country_code("123") is None
    True
    """
    if value is None:
        return None
    cleaned = value.strip().upper()
    return cleaned if re.fullmatch(r"[A-Z]{2}", cleaned) else None


def parse_iso_timestamp(value: Optional[str]) -> Optional[datetime]:
    """
    Parses ISO 8601 timestamp string to datetime.
    Returns None on failure — never raises.

    >>> parse_iso_timestamp("2024-01-15T10:30:00Z")
    datetime.datetime(2024, 1, 15, 10, 30)
    >>> parse_iso_timestamp("bad-date") is None
    True
    """
    if not value:
        return None
    for fmt in (
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%S"
    ):
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def is_valid_event_type(event_type: Optional[str]) -> bool:
    """
    Returns True if event_type is one of the known clickstream event types.

    >>> is_valid_event_type("purchase")
    True
    >>> is_valid_event_type("unknown")
    False
    """
    valid = {
        "page_view", "product_view", "add_to_cart",
        "remove_from_cart", "checkout_start", "purchase", "search"
    }
    return event_type in valid


def calculate_cart_abandonment_rate(
    add_to_cart_count: int, purchase_count: int
) -> Optional[float]:
    """
    Returns abandonment rate as a percentage.
    Returns None if no carts to avoid division by zero.

    >>> calculate_cart_abandonment_rate(100, 25)
    75.0
    >>> calculate_cart_abandonment_rate(0, 0) is None
    True
    """
    if add_to_cart_count == 0:
        return None
    return round(
        (add_to_cart_count - purchase_count) / add_to_cart_count * 100, 2
    )


def calculate_conversion_rate(
    sessions: int, purchases: int
) -> Optional[float]:
    """
    Returns session-to-purchase conversion rate as a percentage.

    >>> calculate_conversion_rate(1000, 35)
    3.5
    >>> calculate_conversion_rate(0, 0) is None
    True
    """
    if sessions == 0:
        return None
    return round((purchases / sessions) * 100, 2)


def mask_user_id(user_id: Optional[str]) -> Optional[str]:
    """
    Masks user ID for non-prod environments.
    Keeps first 2 chars, replaces rest with asterisks.

    >>> mask_user_id("U1234")
    'U1***'
    >>> mask_user_id(None) is None
    True
    """
    if user_id is None or len(user_id) <= 2:
        return user_id
    return user_id[:2] + "*" * (len(user_id) - 2)


# ── PySpark DataFrame transformers (used directly in notebooks) ───────────────

def apply_silver_cleaning(df):
    """
    Full silver cleaning logic. Import and call this in the silver notebook
    instead of inlining logic there — keeps notebooks thin and this testable.

    Expects bronze clickstream DataFrame with parsed JSON columns.
    Returns cleaned DataFrame with derived columns added.
    """
    from pyspark.sql import functions as F

    return (
        df
        .withColumn("event_timestamp", F.to_timestamp("event_timestamp"))
        .filter(F.col("event_id").isNotNull())
        .filter(F.col("event_type").isNotNull())
        .filter(F.col("event_timestamp").isNotNull())
        .withColumn("device_type", F.lower(F.trim(F.col("device_type"))))
        .withColumn("browser",     F.lower(F.trim(F.col("browser"))))
        .withColumn("os",          F.lower(F.trim(F.col("os"))))
        .withColumn("country",     F.upper(F.trim(F.col("country"))))
        .withColumn("city",        F.initcap(F.trim(F.col("city"))))
        .withColumn("event_date",  F.to_date("event_timestamp"))
        .withColumn("event_hour",  F.hour("event_timestamp"))
        .withColumn("event_year",  F.year("event_timestamp"))
        .withColumn("event_month", F.month("event_timestamp"))
        .withColumn("is_purchase", F.col("event_type") == "purchase")
        .withColumn("has_product", F.col("product_id").isNotNull())
    )


def apply_gold_daily_kpis(df):
    """
    Aggregates silver data into daily KPI metrics.
    Returns a DataFrame ready to write to gold.daily_ecommerce_kpis.
    """
    from pyspark.sql import functions as F

    return (
        df.groupBy("event_date")
        .agg(
            F.countDistinct("session_id").alias("total_sessions"),
            F.countDistinct("user_id").alias("unique_users"),
            F.count("event_id").alias("total_events"),
            F.sum(F.when(
                F.col("event_type") == "purchase", F.col("revenue")
            )).alias("total_revenue"),
            F.sum(F.when(
                F.col("event_type") == "purchase", 1
            ).otherwise(0)).alias("total_purchases"),
            F.sum(F.when(
                F.col("event_type") == "add_to_cart", 1
            ).otherwise(0)).alias("add_to_cart_count"),
            F.sum(F.when(
                F.col("event_type") == "page_view", 1
            ).otherwise(0)).alias("page_views"),
            F.avg(F.when(
                F.col("event_type") == "purchase", F.col("revenue")
            )).alias("avg_order_value"),
        )
        .withColumn(
            "conversion_rate",
            F.round(
                F.col("total_purchases") / F.col("total_sessions") * 100, 2
            )
        )
        .withColumn(
            "cart_abandonment_rate",
            F.round(
                (F.col("add_to_cart_count") - F.col("total_purchases"))
                / F.col("add_to_cart_count") * 100, 2
            )
        )
        .withColumn("avg_order_value", F.round(F.col("avg_order_value"), 2))
    )


def apply_gold_product_performance(df):
    """
    Aggregates silver data into product-level performance metrics.
    Returns a DataFrame ready to write to gold.product_performance.
    """
    from pyspark.sql import functions as F

    return (
        df
        .filter(F.col("product_id").isNotNull())
        .groupBy("event_date", "product_id", "product_name", "product_category")
        .agg(
            F.sum(F.when(
                F.col("event_type") == "product_view", 1
            ).otherwise(0)).alias("product_views"),
            F.sum(F.when(
                F.col("event_type") == "add_to_cart", 1
            ).otherwise(0)).alias("add_to_carts"),
            F.sum(F.when(
                F.col("event_type") == "purchase", 1
            ).otherwise(0)).alias("purchases"),
            F.sum(F.when(
                F.col("event_type") == "purchase", F.col("revenue")
            )).alias("revenue"),
            F.sum(F.when(
                F.col("event_type") == "purchase", F.col("quantity")
            )).alias("units_sold"),
            F.avg(F.col("product_price")).alias("product_price"),
        )
        .withColumn(
            "view_to_cart_rate",
            F.round(F.col("add_to_carts") / F.col("product_views") * 100, 2)
        )
        .withColumn(
            "cart_to_purchase_rate",
            F.round(F.col("purchases") / F.col("add_to_carts") * 100, 2)
        )
    )
