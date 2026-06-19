# 1. Register the Service Principal at the Databricks ACCOUNT level
resource "databricks_service_principal" "dbt_account_sp" {
  provider       = databricks.accounts
  application_id = var.dbt_sp_application_id
  display_name   = "sp-dbt-analytics-${var.environment}"
}

# 2. Assign that Account-Level SP to this specific WORKSPACE
resource "databricks_mws_permission_assignment" "dbt_workspace_mapping" {
  provider     = databricks.accounts
  workspace_id = azurerm_databricks_workspace.main.workspace_id # <-- REVERT BACK TO THIS
  principal_id = databricks_service_principal.dbt_account_sp.id
  permissions  = ["USER"]
}

# 3. Generate an OAuth Token or Personal Access Token (OBO - On-Behalf-Of Token)
resource "databricks_token" "dbt_sp_token" {
  provider         = databricks.workspace
  comment          = "Automated pipeline token for dbt Core execution"
  lifetime_seconds = 2592000 # 30 Days
  
  depends_on = [databricks_mws_permission_assignment.dbt_workspace_mapping]
}