terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.85"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.35"
    }
  }

  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "stdbricsanaltrfrm"
    container_name       = "tfstate"
    key                  = "dev.terraform.tfstate"
  }
}

provider "azurerm" {
  features {
    resource_group {
      # CRITICAL: Fixes the "RG not empty" error by forcing deletion of hidden resources
      prevent_deletion_if_contains_resources = false
    }
    key_vault {
      # Ensures you don't get "Name already exists" errors on re-run
      purge_soft_delete_on_destroy = true
    }
  }
}

resource "azurerm_resource_group" "main" {
  name     = "rg-databricks-analytics-${var.environment}"
  location = var.location
}

# This provider allows Terraform to "log in" to Databricks to set up Unity Catalog
provider "databricks" {
  host = module.databricks.workspace_url
  # The agent on your laptop will use your Azure CLI login to authenticate
}
module "keyvault" {
  source              = "../../modules/keyvault"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  environment         = var.environment
  tenant_id           = var.tenant_id
}

module "storage" {
  source              = "../../modules/storage"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  environment         = var.environment
}

module "eventhubs" {
  source              = "../../modules/eventhubs"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  environment         = var.environment
  keyvault_id         = module.keyvault.keyvault_id
}

module "databricks" {
  source              = "../../modules/databricks"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  environment         = var.environment
}

module "unity_catalog" {
  source              = "../../modules/unity_catalog"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  environment         = var.environment
  
  # Dependencies: Passes IDs from your other modules
  databricks_workspace_id = module.databricks.workspace_id
  storage_account_id      = module.storage.storage_account_id
  storage_account_name    = module.storage.storage_account_name
  access_connector_id     = module.databricks.access_connector_id
  principal_id            = module.databricks.principal_id
}