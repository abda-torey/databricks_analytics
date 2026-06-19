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

output "sql_warehouse_hostname" {
  value       = databricks_sql_endpoint.dbt_compute.odbc_params[0].hostname
  description = "The SQL Warehouse Hostname for dbt connection"
}

output "sql_warehouse_http_path" {
  value       = databricks_sql_endpoint.dbt_compute.odbc_params[0].path
  description = "The SQL Warehouse HTTP path for dbt connection"
}



# NEW: Exposed outputs matching your root module assignments
output "dbt_sp_application_id" {
  value       = databricks_service_principal.dbt_account_sp.application_id
  description = "The application ID for the registered dbt Service Principal"
}

output "dbt_token_value" {
  value       = databricks_token.dbt_sp_token.token_value
  sensitive   = true # Prevents the token string from printing in plain text to terminal logs
  description = "The raw secret token generated for the dbt service principal"
}