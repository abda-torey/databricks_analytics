resource "azurerm_eventhub_namespace" "main" {
  name                = "evhns-databrksanlytc-${var.environment}"
  location            = var.location
  resource_group_name = var.resource_group_name
  sku                 = "Standard"
  capacity            = 1
  tags = { environment = var.environment, project = "databricks-analytics" }
}

resource "azurerm_eventhub" "clickstream" {
  name                = "clickstream-events"
  namespace_name      = azurerm_eventhub_namespace.main.name
  resource_group_name = var.resource_group_name
  partition_count     = 4
  message_retention   = 1
}

resource "azurerm_eventhub_authorization_rule" "producer" {
  name                = "clickstream-producer"
  namespace_name      = azurerm_eventhub_namespace.main.name
  eventhub_name       = azurerm_eventhub.clickstream.name
  resource_group_name = var.resource_group_name
  listen = false
  send   = true
  manage = false
}

resource "azurerm_eventhub_authorization_rule" "consumer" {
  name                = "clickstream-consumer"
  namespace_name      = azurerm_eventhub_namespace.main.name
  eventhub_name       = azurerm_eventhub.clickstream.name
  resource_group_name = var.resource_group_name
  listen = true
  send   = false
  manage = false
}

resource "azurerm_key_vault_secret" "producer_conn" {
  name         = "eventhub-producer-connection-string"
  value        = azurerm_eventhub_authorization_rule.producer.primary_connection_string
  key_vault_id = var.keyvault_id
}

resource "azurerm_key_vault_secret" "consumer_conn" {
  name         = "eventhub-consumer-connection-string"
  value        = azurerm_eventhub_authorization_rule.consumer.primary_connection_string
  key_vault_id = var.keyvault_id
}

output "eventhub_namespace" { value = azurerm_eventhub_namespace.main.name }
output "eventhub_name"      { value = azurerm_eventhub.clickstream.name }