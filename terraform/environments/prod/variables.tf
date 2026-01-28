# =============================================================================
# Production Environment - Variables
# =============================================================================

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "bees-breweries"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "prod"
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
  default     = "10.1.0.0/16" # Different CIDR from dev to allow VPC peering if needed
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
  description = "Master password for PostgreSQL (MUST use AWS Secrets Manager in production)"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.db_password) >= 16
    error_message = "Production database password must be at least 16 characters"
  }
}
