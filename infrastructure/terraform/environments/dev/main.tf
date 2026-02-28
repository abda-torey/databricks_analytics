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
  features {}
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