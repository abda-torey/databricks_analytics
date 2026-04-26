variable "environment" {
  description = "Deployment environment"
  default     = "dev"
}

variable "location" {
  description = "Azure region"
  default     = "eastus"
}

variable "tenant_id" {
  description = "Azure AD Tenant ID"
  type        = string
}

variable "subscription_id" {
  description = "Azure Subscription ID"
  type        = string
}

variable "databricks_account_id" {
  description = "Databricks Account ID — found at accounts.azuredatabricks.net top-right corner"
  type        = string
}
variable "pipeline_sp_object_id" {
  description = "Object ID of the pipeline SP"
}