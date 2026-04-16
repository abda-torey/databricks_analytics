terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.85"
    }
    databricks = {
      source                = "databricks/databricks"
      version               = "~> 1.35"
      configuration_aliases = [databricks.accounts, databricks.workspace]
    }
  }
}

# ── IAM: Give the access connector permission to read/write ADLS ──────────────
resource "azurerm_role_assignment" "unity_storage" {
  scope                = var.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.principal_id
}

# ── Metastore (account-level) ─────────────────────────────────────────────────
resource "databricks_metastore" "this" {
  provider     = databricks.accounts
  name         = "metastore-megaec-${var.environment}"
  region       = var.location
  storage_root = "abfss://unity-catalog@${var.storage_account_name}.dfs.core.windows.net/metastore"
  force_destroy = true

  depends_on = [azurerm_role_assignment.unity_storage]
}

# ── Metastore data access: link the connector to the metastore ────────────────
resource "databricks_metastore_data_access" "this" {
  provider     = databricks.accounts
  metastore_id = databricks_metastore.this.id
  name         = "megaec-${var.environment}-access"
  is_default   = true

  azure_managed_identity {
    access_connector_id = var.access_connector_id
  }
}

# ── Assign the metastore to the workspace ─────────────────────────────────────
resource "databricks_metastore_assignment" "this" {
  provider             = databricks.accounts
  metastore_id         = databricks_metastore.this.id
  workspace_id         = var.databricks_workspace_id
  default_catalog_name = "${var.environment}_catalog"
}

# ── Storage credential (workspace-level) ─────────────────────────────────────
resource "databricks_storage_credential" "this" {
  provider = databricks.workspace
  name     = "megaec-${var.environment}-credential"

  azure_managed_identity {
    access_connector_id = var.access_connector_id
  }

  comment    = "Managed identity credential for ${var.environment}"
  depends_on = [databricks_metastore_assignment.this]
}

# ── External locations ────────────────────────────────────────────────────────
resource "databricks_external_location" "bronze" {
  provider        = databricks.workspace
  name            = "bronze_location"
  url             = "abfss://bronze@${var.storage_account_name}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.this.name
  comment         = "Raw ingestion layer"
}

resource "databricks_external_location" "silver" {
  provider        = databricks.workspace
  name            = "silver_location"
  url             = "abfss://silver@${var.storage_account_name}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.this.name
  comment         = "Cleaned and enriched layer"
}

resource "databricks_external_location" "gold" {
  provider        = databricks.workspace
  name            = "gold_location"
  url             = "abfss://gold@${var.storage_account_name}.dfs.core.windows.net/"
  credential_name = databricks_storage_credential.this.name
  comment         = "Business aggregates and KPIs"
}

# ── Catalog ───────────────────────────────────────────────────────────────────
resource "databricks_catalog" "this" {
  provider     = databricks.workspace
  name         = "${var.environment}_catalog"
  metastore_id = databricks_metastore.this.id
  comment      = "Main catalog for ${var.environment} environment"

  depends_on = [databricks_metastore_assignment.this]
}

# ── Schemas ───────────────────────────────────────────────────────────────────
resource "databricks_schema" "bronze" {
  provider     = databricks.workspace
  catalog_name = databricks_catalog.this.name
  name         = "bronze"
  comment      = "Raw ingestion layer"
}

resource "databricks_schema" "silver" {
  provider     = databricks.workspace
  catalog_name = databricks_catalog.this.name
  name         = "silver"
  comment      = "Cleaned and enriched layer"
}

resource "databricks_schema" "gold" {
  provider     = databricks.workspace
  catalog_name = databricks_catalog.this.name
  name         = "gold"
  comment      = "Business aggregates and KPIs"
}