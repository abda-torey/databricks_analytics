variable "resource_group_name" {
  description = "Name of the resource group"
  type        = string
}

variable "location" {
  description = "Azure region where the resources exist"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, prod, etc.)"
  type        = string
}

variable "databricks_workspace_id" {
  description = "The ID of the Databricks Workspace (used for metastore assignment)"
  type        = string
}

variable "storage_account_id" {
  description = "The Resource ID of the ADLS Gen2 Storage Account for IAM role assignment"
  type        = string
}

variable "storage_account_name" {
  description = "The name of the Storage Account for the storage root path"
  type        = string
}

variable "access_connector_id" {
  description = "The Resource ID of the Azure Databricks Access Connector"
  type        = string
}

variable "principal_id" {
  description = "The Managed Identity Principal ID of the Access Connector for IAM role assignment"
  type        = string
}
variable "workspace_admin_email" {
  description = "Email of personal account that needs catalog and external location access"
  type        = string
  default     = "databricks@abda5685hotmail.onmicrosoft.com"
}