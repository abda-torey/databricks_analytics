data "azurerm_client_config" "current" {}

# ==========================================
# 1. MICROSOFT ENTRA ID (AZURE AD) IDENTITY
# ==========================================

# Create the Application Registration for dbt
resource "azuread_application" "dbt_sp" {
  display_name = "sp-dbt-analytics-${var.environment}"
}

# Create the corresponding Service Principal identity
resource "azuread_service_principal" "dbt_sp" {
  client_id = azuread_application.dbt_sp.client_id
}

# Programmatically generate a secure password for the SP
resource "azuread_service_principal_password" "dbt_sp_password" {
  service_principal_id = azuread_service_principal.dbt_sp.id
  end_date             = "2028-01-01T00:00:00Z"
}

# ==========================================
# 2. KEY VAULT CORE RESOURCE
# ==========================================

resource "azurerm_key_vault" "main" {
  name                       = "kv-databrksanlytc-${var.environment}"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  tenant_id                  = var.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false

  # SP running Terraform — full access to create/delete secrets
  access_policy {
    tenant_id          = var.tenant_id
    object_id          = data.azurerm_client_config.current.object_id
    secret_permissions = ["Get", "List", "Set", "Delete", "Purge"]
  }

  # AzureDatabricks internal app — needed for secret scopes to work
  access_policy {
    tenant_id          = var.tenant_id
    object_id          = "babc80ee-75cd-4c8b-bf8c-4bc8bf325cb8"
    secret_permissions = ["Get", "List"]
  }

  # Your personal account — needed to run data generator locally
  access_policy {
    tenant_id          = var.tenant_id
    object_id          = "00c33728-0a86-44ec-9205-c67aa70efc54"
    secret_permissions = ["Get", "List"]
  }

  tags = {
    environment = var.environment
    project     = "databricks-analytics"
  }
}

# ==========================================
# 3. AUTOMATED SECRET PROVISIONING
# ==========================================

# FIX 1: Save the Databricks token passed from the root module
resource "azurerm_key_vault_secret" "dbt_databricks_token" {
  name         = "dbt-databricks-token"
  value        = var.dbt_token_value
  key_vault_id = azurerm_key_vault.main.id # Reference the local vault directly
}

# FIX 2: Save the Client ID by reading the local azuread resource directly
resource "azurerm_key_vault_secret" "dbt_sp_client_id" {
  name         = "dbt-sp-client-id"
  value        = azuread_application.dbt_sp.client_id # Native resource reference
  key_vault_id = azurerm_key_vault.main.id # Reference the local vault directly
}

# Save the Client Secret (Password) generated locally
resource "azurerm_key_vault_secret" "dbt_sp_client_secret" {
  name         = "dbt-sp-client-secret"
  value        = azuread_service_principal_password.dbt_sp_password.value
  key_vault_id = azurerm_key_vault.main.id
}

# ==========================================
# 4. MODULE OUTPUTS
# ==========================================

output "keyvault_id"   { value = azurerm_key_vault.main.id }
output "keyvault_uri"  { value = azurerm_key_vault.main.vault_uri }
output "dbt_sp_client_id" { value = azuread_application.dbt_sp.client_id }