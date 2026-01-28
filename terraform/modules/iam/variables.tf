# =============================================================================
# IAM Module - Variables
# =============================================================================

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

# -----------------------------------------------------------------------------
# S3 Bucket Configuration
# -----------------------------------------------------------------------------

variable "airflow_bucket_arn" {
  description = "ARN of the S3 bucket containing Airflow DAGs and plugins"
  type        = string
}

variable "data_bucket_arns" {
  description = "List of S3 bucket ARNs for data lake (bronze, silver, gold)"
  type        = list(string)
  default     = []
}

# -----------------------------------------------------------------------------
# Feature Flags
# -----------------------------------------------------------------------------

variable "enable_rds_access" {
  description = "Enable RDS access policy for MWAA role"
  type        = bool
  default     = true
}

variable "enable_secrets_manager_access" {
  description = "Enable Secrets Manager access for retrieving credentials"
  type        = bool
  default     = false
}

variable "create_rds_monitoring_role" {
  description = "Create IAM role for RDS enhanced monitoring"
  type        = bool
  default     = false
}

# -----------------------------------------------------------------------------
# Common Tags
# -----------------------------------------------------------------------------

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
