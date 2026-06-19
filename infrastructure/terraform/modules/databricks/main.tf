
terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.85"
    }
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.35"
      configuration_aliases = [ databricks.workspace,databricks.accounts ]
    }
  }
}


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

resource "databricks_sql_endpoint" "dbt_compute" {
  provider = databricks.workspace
  name             = "dbt-sql-warehouse-${var.environment}"
  cluster_size     = "2X-Small"
  max_num_clusters = 1
  auto_stop_mins   = 10
  enable_serverless_compute = true # Serverless is best for dbt
  tags {
    custom_tags {
      key   = "used_by"
      value = "dbt_cloud"
    }
  }
}