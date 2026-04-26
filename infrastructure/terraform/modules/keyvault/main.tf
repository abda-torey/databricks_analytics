data "azurerm_client_config" "current" {}

resource "azurerm_key_vault" "main" {
  name                       = "kv-databrksanlytc-${var.environment}"
  location                   = var.location
  resource_group_name        = var.resource_group_name
  tenant_id                  = var.tenant_id
  sku_name                   = "standard"
  soft_delete_retention_days = 7
  purge_protection_enabled   = false

  access_policy {
    tenant_id = var.tenant_id
    object_id = data.azurerm_client_config.current.object_id

    secret_permissions = ["Get", "List", "Set", "Delete", "Purge"]
  }

 

  tags = {
    environment = var.environment
    project     = "databricks-analytics"
  }
}

output "keyvault_id"  { value = azurerm_key_vault.main.id }
output "keyvault_uri" { value = azurerm_key_vault.main.vault_uri }