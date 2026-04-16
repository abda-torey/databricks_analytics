resource "azurerm_databricks_workspace" "main" {
  name                = "dbw-megaec-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location
  sku                 = "premium"

  tags = {
    environment = var.environment
    project     = "mega-ecommerce"
  }
}

# Access connector lives here — unity_catalog module consumes it
resource "azurerm_databricks_access_connector" "unity" {
  name                = "ac-megaec-${var.environment}"
  resource_group_name = var.resource_group_name
  location            = var.location

  identity {
    type = "SystemAssigned"
  }

  tags = {
    environment = var.environment
    project     = "mega-ecommerce"
  }
}