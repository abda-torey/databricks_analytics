variable "resource_group_name"    {}
variable "location"               {}
variable "environment"            {}
variable "tenant_id"              {}
variable "pipeline_sp_object_id" {
  description = "Object ID of the SP running the pipeline — needs Key Vault secret access"
}
variable "dbt_token_value" {
  type        = string
  sensitive   = true # Redacts the token from leaking into plan/apply CLI logs
  description = "The raw secret token string from Databricks to back into Key Vault"
}

