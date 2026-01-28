# =============================================================================
# Database Module - Variables
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
# RDS Instance Configuration
# -----------------------------------------------------------------------------

variable "instance_class" {
  description = "RDS instance class (e.g., db.t3.micro for dev, db.t3.medium for prod)"
  type        = string
}

variable "engine_version" {
  description = "PostgreSQL engine version"
  type        = string
  default     = "15.4"
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20

  validation {
    condition     = var.allocated_storage >= 20 && var.allocated_storage <= 65536
    error_message = "Allocated storage must be between 20 GB and 65536 GB"
  }
}

variable "storage_type" {
  description = "Storage type (gp2, gp3, io1)"
  type        = string
  default     = "gp3"
}

# -----------------------------------------------------------------------------
# Database Configuration
# -----------------------------------------------------------------------------

variable "db_name" {
  description = "Name of the default database to create"
  type        = string
  default     = "airflow"
}

variable "db_username" {
  description = "Master username for the database"
  type        = string
  default     = "airflow"
}

variable "db_password" {
  description = "Master password for the database (use AWS Secrets Manager in production)"
  type        = string
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Network Configuration
# -----------------------------------------------------------------------------

variable "subnet_ids" {
  description = "List of subnet IDs for DB subnet group (minimum 2 required)"
  type        = list(string)
}

variable "security_group_ids" {
  description = "List of security group IDs to attach to the RDS instance"
  type        = list(string)
}

# -----------------------------------------------------------------------------
# High Availability and Backup
# -----------------------------------------------------------------------------

variable "multi_az" {
  description = "Enable multi-AZ deployment for high availability (recommended for prod)"
  type        = bool
  default     = false
}

variable "backup_retention_days" {
  description = "Number of days to retain automated backups (0-35)"
  type        = number
  default     = 7

  validation {
    condition     = var.backup_retention_days >= 0 && var.backup_retention_days <= 35
    error_message = "Backup retention must be between 0 and 35 days"
  }
}

variable "backup_window" {
  description = "Preferred backup window (UTC)"
  type        = string
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  description = "Preferred maintenance window (UTC)"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

# -----------------------------------------------------------------------------
# Deletion and Snapshot Configuration
# -----------------------------------------------------------------------------

variable "skip_final_snapshot" {
  description = "Skip final snapshot when destroying (set to false for prod)"
  type        = bool
  default     = true
}

variable "deletion_protection" {
  description = "Enable deletion protection (recommended for prod)"
  type        = bool
  default     = false
}

# -----------------------------------------------------------------------------
# Monitoring Configuration
# -----------------------------------------------------------------------------

variable "enhanced_monitoring_interval" {
  description = "Enhanced monitoring interval in seconds (0, 1, 5, 10, 15, 30, 60)"
  type        = number
  default     = 0

  validation {
    condition     = contains([0, 1, 5, 10, 15, 30, 60], var.enhanced_monitoring_interval)
    error_message = "Enhanced monitoring interval must be 0, 1, 5, 10, 15, 30, or 60 seconds"
  }
}

variable "monitoring_role_arn" {
  description = "IAM role ARN for enhanced monitoring (required if enhanced_monitoring_interval > 0)"
  type        = string
  default     = ""
}

variable "enable_performance_insights" {
  description = "Enable Performance Insights (additional cost)"
  type        = bool
  default     = false
}

# -----------------------------------------------------------------------------
# Performance Configuration
# -----------------------------------------------------------------------------

variable "work_mem_kb" {
  description = "PostgreSQL work_mem parameter in KB (affects query performance)"
  type        = string
  default     = "4096" # 4 MB default
}

# -----------------------------------------------------------------------------
# Common Tags
# -----------------------------------------------------------------------------

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
