# =============================================================================
# Development Environment - Variables
# =============================================================================

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "bees-breweries"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

# -----------------------------------------------------------------------------
# Networking Variables
# -----------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# -----------------------------------------------------------------------------
# Database Variables
# -----------------------------------------------------------------------------

variable "db_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "airflow"
}

variable "db_username" {
  description = "Master username for PostgreSQL"
  type        = string
  default     = "airflow"
}

variable "db_password" {
  description = "Master password for PostgreSQL (should be in terraform.tfvars, not committed)"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.db_password) >= 8
    error_message = "Database password must be at least 8 characters"
  }
}
