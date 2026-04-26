resource "azurerm_storage_account" "adls" {
  name                     = "databrksanlytc${var.environment}"
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  account_kind             = "StorageV2"
  is_hns_enabled           = true

  tags = { environment = var.environment, project = "databricks-analytics" }
}

resource "azurerm_storage_container" "bronze"      {
  name                  = "bronze"
  storage_account_name  = azurerm_storage_account.adls.name
  container_access_type = "private"
}
resource "azurerm_storage_container" "silver"      {
  name                  = "silver"
  storage_account_name  = azurerm_storage_account.adls.name
  container_access_type = "private"
}
resource "azurerm_storage_container" "gold"        {
  name                  = "gold"
  storage_account_name  = azurerm_storage_account.adls.name
  container_access_type = "private"
}
resource "azurerm_storage_container" "unity_catalog" {
  name                  = "unity-catalog"
  storage_account_name  = azurerm_storage_account.adls.name
  container_access_type = "private"
}

output "storage_account_name" { value = azurerm_storage_account.adls.name }
output "storage_account_id"   { value = azurerm_storage_account.adls.id }
output "dfs_endpoint"         { value = azurerm_storage_account.adls.primary_dfs_endpoint }