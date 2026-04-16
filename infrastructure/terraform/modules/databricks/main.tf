resource "azurerm_databricks_workspace" "main" {
  name                = "dbw-databrksanlytc-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "premium" # Required for Unity Catalog
}

# The "Passport" for Databricks to talk to Azure Storage
resource "azurerm_databricks_access_connector" "main" {
  name                = "ac-databricksanlytc-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  identity { type = "SystemAssigned" }
}

output "access_connector_id" { value = azurerm_databricks_access_connector.main.id }
output "principal_id"        { value = azurerm_databricks_access_connector.main.identity[0].principal_id }

output "workspace_url" { value = azurerm_databricks_workspace.main.workspace_url }
output "workspace_id"  { value = azurerm_databricks_workspace.main.workspace_id }
output "resource_id"   { value = azurerm_databricks_workspace.main.id }