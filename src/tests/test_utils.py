# src/tests/test_utils.py
import pytest
from src.common.utils import (
    get_env_config,
    get_storage_path,
    get_table_name,
    build_job_metadata,
)


class TestGetEnvConfig:
    def test_dev_catalog(self):
        assert get_env_config("dev")["catalog"] == "dev_catalog"

    def test_staging_catalog(self):
        assert get_env_config("staging")["catalog"] == "stg_catalog"

    def test_prod_catalog(self):
        assert get_env_config("prod")["catalog"] == "prod_catalog"

    def test_unknown_env_raises(self):
        with pytest.raises(ValueError, match="Unknown environment"):
            get_env_config("uat")

    def test_case_insensitive(self):
        assert get_env_config("DEV")["catalog"] == "dev_catalog"

    def test_has_required_keys(self):
        cfg = get_env_config("dev")
        for key in ["catalog", "storage_account", "keyvault_uri", "secret_scope"]:
            assert key in cfg

    def test_dev_storage_account(self):
        assert get_env_config("dev")["storage_account"] == "databrksanlytcdev"

    def test_prod_log_level(self):
        assert get_env_config("prod")["log_level"] == "WARNING"


class TestGetStoragePath:
    def test_bronze_dev(self):
        path = get_storage_path("dev", "bronze", "clickstream")
        assert path == "abfss://bronze@databrksanlytcdev.dfs.core.windows.net/clickstream"

    def test_gold_prod(self):
        path = get_storage_path("prod", "gold", "daily_kpis")
        assert path == "abfss://gold@databrksanlytcprod.dfs.core.windows.net/daily_kpis"

    def test_no_dataset(self):
        path = get_storage_path("dev", "silver")
        assert path == "abfss://silver@databrksanlytcdev.dfs.core.windows.net"

    def test_checkpoint_path(self):
        path = get_storage_path("dev", "bronze", "_checkpoints/clickstream")
        assert "_checkpoints/clickstream" in path

    def test_staging_storage_account(self):
        path = get_storage_path("staging", "bronze", "data")
        assert "databrksanlytcstg" in path


class TestGetTableName:
    def test_bronze_table(self):
        assert get_table_name("dev", "bronze", "clickstream_raw") \
               == "dev_catalog.bronze.clickstream_raw"

    def test_gold_table(self):
        assert get_table_name("prod", "gold", "daily_ecommerce_kpis") \
               == "prod_catalog.gold.daily_ecommerce_kpis"

    def test_silver_staging(self):
        assert get_table_name("staging", "silver", "clickstream_clean") \
               == "stg_catalog.silver.clickstream_clean"


class TestBuildJobMetadata:
    def test_has_required_keys(self):
        meta = build_job_metadata("dev", "bronze_clickstream", "bronze")
        assert meta["job_name"] == "bronze_clickstream"
        assert meta["layer"] == "bronze"
        assert meta["environment"] == "dev"
        assert "run_time" in meta

    def test_run_time_ends_with_z(self):
        meta = build_job_metadata("dev", "test", "silver")
        assert meta["run_time"].endswith("Z")

    def test_all_environments(self):
        for env in ["dev", "staging", "prod"]:
            meta = build_job_metadata(env, "test_job", "gold")
            assert meta["environment"] == env
