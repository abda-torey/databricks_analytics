data "azurerm_client_config" "current" {}

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

output "keyvault_id"  { value = azurerm_key_vault.main.id }
output "keyvault_uri" { value = azurerm_key_vault.main.vault_uri }