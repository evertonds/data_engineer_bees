# =============================================================================
# Airflow Module - Variables
# =============================================================================

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID for resource policies"
  type        = string
}

variable "airflow_bucket_name" {
  description = "Name of the S3 bucket for Airflow DAGs (created in storage module)"
  type        = string
}

variable "airflow_bucket_arn" {
  description = "ARN of the S3 bucket for Airflow DAGs (created in storage module)"
  type        = string
}

# -----------------------------------------------------------------------------
# MWAA Environment Configuration
# -----------------------------------------------------------------------------

variable "airflow_version" {
  description = "Apache Airflow version"
  type        = string
  default     = "2.7.2"
}

variable "environment_class" {
  description = "Environment class (mw1.small, mw1.medium, mw1.large)"
  type        = string

  validation {
    condition     = contains(["mw1.small", "mw1.medium", "mw1.large"], var.environment_class)
    error_message = "Environment class must be mw1.small, mw1.medium, or mw1.large"
  }
}

# -----------------------------------------------------------------------------
# Scaling Configuration
# -----------------------------------------------------------------------------

variable "min_workers" {
  description = "Minimum number of Airflow workers"
  type        = number
  default     = 1

  validation {
    condition     = var.min_workers >= 1 && var.min_workers <= 25
    error_message = "Min workers must be between 1 and 25"
  }
}

variable "max_workers" {
  description = "Maximum number of Airflow workers (auto-scaling)"
  type        = number
  default     = 10

  validation {
    condition     = var.max_workers >= 1 && var.max_workers <= 25
    error_message = "Max workers must be between 1 and 25"
  }
}

variable "schedulers_count" {
  description = "Number of Airflow schedulers (2-5, more schedulers = better performance)"
  type        = number
  default     = 2

  validation {
    condition     = var.schedulers_count >= 2 && var.schedulers_count <= 5
    error_message = "Schedulers count must be between 2 and 5"
  }
}

# -----------------------------------------------------------------------------
# Network Configuration
# -----------------------------------------------------------------------------

variable "subnet_ids" {
  description = "List of private subnet IDs for MWAA (minimum 2 required in different AZs)"
  type        = list(string)
}

variable "security_group_ids" {
  description = "List of security group IDs for MWAA"
  type        = list(string)
}

variable "execution_role_arn" {
  description = "IAM role ARN for MWAA execution"
  type        = string
}

# -----------------------------------------------------------------------------
# Logging Configuration
# -----------------------------------------------------------------------------

variable "log_retention_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 7

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention must be a valid CloudWatch retention period"
  }
}

variable "dag_processing_log_level" {
  description = "Log level for DAG processing (CRITICAL, ERROR, WARNING, INFO, DEBUG)"
  type        = string
  default     = "INFO"
}

variable "scheduler_log_level" {
  description = "Log level for scheduler logs"
  type        = string
  default     = "INFO"
}

variable "task_log_level" {
  description = "Log level for task logs"
  type        = string
  default     = "INFO"
}

variable "webserver_log_level" {
  description = "Log level for webserver logs"
  type        = string
  default     = "INFO"
}

variable "worker_log_level" {
  description = "Log level for worker logs"
  type        = string
  default     = "INFO"
}

# -----------------------------------------------------------------------------
# Airflow Configuration Options
# -----------------------------------------------------------------------------

variable "dag_concurrency" {
  description = "Maximum number of task instances that can run concurrently per DAG"
  type        = number
  default     = 16
}

variable "parallelism" {
  description = "Maximum number of task instances that can run concurrently across all DAGs"
  type        = number
  default     = 32
}

variable "max_active_runs_per_dag" {
  description = "Maximum number of active DAG runs per DAG"
  type        = number
  default     = 3
}

variable "additional_airflow_config" {
  description = "Additional Airflow configuration options (airflow.cfg format)"
  type        = map(string)
  default     = {}
}

# -----------------------------------------------------------------------------
# Access Configuration
# -----------------------------------------------------------------------------

variable "webserver_access_mode" {
  description = "Airflow webserver access mode (PUBLIC_ONLY or PRIVATE_ONLY)"
  type        = string
  default     = "PUBLIC_ONLY"

  validation {
    condition     = contains(["PUBLIC_ONLY", "PRIVATE_ONLY"], var.webserver_access_mode)
    error_message = "Webserver access mode must be PUBLIC_ONLY or PRIVATE_ONLY"
  }
}

variable "maintenance_window" {
  description = "Weekly maintenance window (UTC, format: DAY:HH:MM)"
  type        = string
  default     = "SUN:03:00"
}

# -----------------------------------------------------------------------------
# Common Tags
# -----------------------------------------------------------------------------

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
