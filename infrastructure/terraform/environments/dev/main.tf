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
      prevent_deletion_if_contains_resources = false
    }
    key_vault {
      purge_soft_delete_on_destroy = true
    }
  }
}

# Workspace-level Databricks provider
# Uses Azure CLI login on your laptop automatically
provider "databricks" {
  alias = "workspace"
  host  = module.databricks.workspace_url
}

# Account-level Databricks provider
# Talks to accounts.azuredatabricks.net for metastore management
provider "databricks" {
  alias      = "accounts"
  host       = "https://accounts.azuredatabricks.net"
  account_id = var.databricks_account_id
}

resource "azurerm_resource_group" "main" {
  name     = "rg-databricks-analytics-${var.environment}"
  location = var.location
}

module "keyvault" {
  source              = "../../modules/keyvault"
  resource_group_name = azurerm_resource_group.main.name
  location            = var.location
  environment         = var.environment
  tenant_id           = var.tenant_id
  pipeline_sp_object_id = var.pipeline_sp_object_id
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

  databricks_workspace_id = module.databricks.workspace_id
  storage_account_id      = module.storage.storage_account_id
  storage_account_name    = module.storage.storage_account_name
  access_connector_id     = module.databricks.access_connector_id
  principal_id            = module.databricks.principal_id

  # Pass provider aliases into the module
  providers = {
    databricks.accounts  = databricks.accounts
    databricks.workspace = databricks.workspace
  }
}