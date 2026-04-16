# 1. Look for an existing Metastore in this region
data "databricks_metastores" "all" {}

locals {
  # Logic: If a metastore exists in our region, use it. Otherwise, use the one we might create.
  # We filter the list of all metastores by the region we are deploying to.
  existing_metastore_id = lookup({ for m in data.databricks_metastores.all.ids : m => m if contains(split("/", m), var.location) }, var.location, null)
  
  # Use the existing ID if found, otherwise use the new one created below
  metastore_id = local.existing_metastore_id != null ? local.existing_metastore_id : databricks_metastore.main[0].id
}

# 2. Only create the Metastore if it DOESN'T exist (count = 0 or 1)
resource "databricks_metastore" "main" {
  count         = local.existing_metastore_id == null ? 1 : 0
  name          = "ms-databrksanlytc-${var.environment}"
  storage_root  = "abfss://unity-catalog@${var.storage_account_name}.dfs.core.windows.net/"
  region        = var.location
  force_destroy = true
}

# 3. Storage Credential (The Handshake)
# This is unique to YOUR project's Access Connector, so we always create it
resource "databricks_storage_credential" "external" {
  name = "cred-databrksanlytc-${var.environment}"
  azure_managed_identity {
    access_connector_id = var.access_connector_id
  }
  metastore_id = local.metastore_id
}

# 4. Link the Workspace to the Metastore
# This ensures YOUR workspace is added to the regional "Library"
resource "databricks_metastore_assignment" "main" {
  metastore_id = local.metastore_id
  workspace_id = var.databricks_workspace_id
}
resource "azurerm_role_assignment" "unity_storage" {
  scope                = var.storage_account_id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = var.principal_id
}