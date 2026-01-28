# =============================================================================
# Storage Module - Variables
# =============================================================================

variable "project_name" {
  description = "Project name used for resource naming (e.g., bees-breweries)"
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens"
  }
}

variable "environment" {
  description = "Environment name (dev, prod)"
  type        = string

  validation {
    condition     = contains(["dev", "prod"], var.environment)
    error_message = "Environment must be either 'dev' or 'prod'"
  }
}

variable "enable_versioning" {
  description = "Enable S3 bucket versioning for data recovery and audit trail"
  type        = bool
  default     = true
}

variable "enable_lifecycle_rules" {
  description = "Enable lifecycle rules for automatic storage class transitions and cost optimization"
  type        = bool
  default     = true
}

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
