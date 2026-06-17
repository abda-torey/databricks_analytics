output "workspace_url" {
  value = "https://${azurerm_databricks_workspace.main.workspace_url}"
}

output "workspace_id" {
  description = "Numeric workspace ID needed for metastore assignment"
  value       = azurerm_databricks_workspace.main.workspace_id
}

output "resource_id" {
  description = "Full Azure resource ID of the workspace"
  value       = azurerm_databricks_workspace.main.id
}

output "access_connector_id" {
  description = "Full resource ID of the access connector"
  value       = azurerm_databricks_access_connector.unity.id
}

output "principal_id" {
  description = "Managed identity principal ID for IAM role assignments"
  value       = azurerm_databricks_access_connector.unity.identity[0].principal_id
}

output "dbt_sql_warehouse_id" {
  value = databricks_sql_endpoint.dbt_compute.id
}
output "dbt_sql_warehouse_jdbc" {
  value = databricks_sql_endpoint.dbt_compute.jdbc_url
}