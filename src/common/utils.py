# src/common/utils.py
import logging
import datetime
from typing import Any


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Standardised logger for all notebooks and scripts.
    Use this instead of print() everywhere.

    Usage:
        logger = get_logger(__name__)
        logger.info("Bronze ingestion started")
    """
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


_ENV_CONFIGS = {
    "dev": {
        "catalog":         "dev_catalog",
        "storage_account": "databrksanlytcdev",
        "keyvault_uri":    "https://kv-databrksanlytc-dev.vault.azure.net/",
        "eventhub_name":   "clickstream-events",
        "secret_scope":    "megaec-secrets",
        "log_level":       "DEBUG",
    },
    "staging": {
        "catalog":         "stg_catalog",
        "storage_account": "databrksanlytcstg",
        "keyvault_uri":    "https://kv-databrksanlytc-staging.vault.azure.net/",
        "eventhub_name":   "clickstream-events",
        "secret_scope":    "megaec-secrets",
        "log_level":       "INFO",
    },
    "prod": {
        "catalog":         "prod_catalog",
        "storage_account": "databrksanlytcprod",
        "keyvault_uri":    "https://kv-databrksanlytc-prod.vault.azure.net/",
        "eventhub_name":   "clickstream-events",
        "secret_scope":    "megaec-secrets",
        "log_level":       "WARNING",
    },
}


def get_env_config(environment: str) -> dict:
    """
    Returns env-specific config dict.

    Usage:
        cfg = get_env_config("dev")
        print(cfg["catalog"])  # dev_catalog
    """
    env = environment.lower().strip()
    if env not in _ENV_CONFIGS:
        raise ValueError(
            f"Unknown environment '{env}'. Must be one of: {list(_ENV_CONFIGS.keys())}"
        )
    return _ENV_CONFIGS[env]


def get_storage_path(environment: str, layer: str, dataset: str = "") -> str:
    """
    Builds an abfss:// path for a given layer and optional dataset.

    Usage:
        get_storage_path("dev", "bronze", "clickstream")
        # abfss://bronze@databrksanlytcdev.dfs.core.windows.net/clickstream

        get_storage_path("dev", "bronze", "_checkpoints/clickstream")
    """
    cfg = get_env_config(environment)
    account = cfg["storage_account"]
    base = f"abfss://{layer}@{account}.dfs.core.windows.net"
    return f"{base}/{dataset}" if dataset else base


def get_table_name(environment: str, schema: str, table: str) -> str:
    """
    Returns fully qualified Unity Catalog table name.

    Usage:
        get_table_name("dev", "bronze", "clickstream_raw")
        # dev_catalog.bronze.clickstream_raw
    """
    cfg = get_env_config(environment)
    return f"{cfg['catalog']}.{schema}.{table}"


def get_databricks_secret(dbutils: Any, scope: str, key: str) -> str:
    """
    Fetches a secret via Databricks secret scope backed by Key Vault.
    Only call this inside notebooks — dbutils is not available outside.

    Usage:
        conn = get_databricks_secret(
            dbutils, "megaec-secrets", "eventhub-consumer-connection-string"
        )
    """
    return dbutils.secrets.get(scope=scope, key=key)


def build_job_metadata(environment: str, job_name: str, layer: str) -> dict:
    """
    Standard metadata dict to log alongside every pipeline run.

    Usage:
        meta = build_job_metadata("dev", "bronze_clickstream", "bronze")
    """
    return {
        "job_name":    job_name,
        "layer":       layer,
        "environment": environment,
        "run_time":    datetime.datetime.utcnow().isoformat() + "Z",
    }