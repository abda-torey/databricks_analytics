variable "resource_group_name"    {}
variable "location"               {}
variable "environment"            {}
variable "tenant_id"              {}
variable "pipeline_sp_object_id" {
  description = "Object ID of the SP running the pipeline — needs Key Vault secret access"
}