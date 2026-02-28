resource "azurerm_databricks_workspace" "main" {
  name                = "dbw-databrksanlytc-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "premium"
  tags = { environment = var.environment, project = "databricks-analytics" }
}

output "workspace_url" { value = azurerm_databricks_workspace.main.workspace_url }
output "workspace_id"  { value = azurerm_databricks_workspace.main.workspace_id }
output "resource_id"   { value = azurerm_databricks_workspace.main.id }