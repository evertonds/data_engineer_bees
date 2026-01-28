# =============================================================================
# Networking Module - Variables
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
# VPC Configuration
# -----------------------------------------------------------------------------

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block"
  }
}

# -----------------------------------------------------------------------------
# Subnet Configuration
# -----------------------------------------------------------------------------

variable "public_subnet_count" {
  description = "Number of public subnets to create (must be >= 2 for MWAA)"
  type        = number
  default     = 2

  validation {
    condition     = var.public_subnet_count >= 2 && var.public_subnet_count <= 6
    error_message = "Public subnet count must be between 2 and 6"
  }
}

variable "private_subnet_count" {
  description = "Number of private subnets to create (must be >= 2 for RDS Multi-AZ)"
  type        = number
  default     = 2

  validation {
    condition     = var.private_subnet_count >= 2 && var.private_subnet_count <= 6
    error_message = "Private subnet count must be between 2 and 6"
  }
}

# -----------------------------------------------------------------------------
# NAT Gateway Configuration
# -----------------------------------------------------------------------------

variable "enable_nat_gateway" {
  description = "Enable NAT gateway for private subnet internet access (recommended for prod, expensive)"
  type        = bool
  default     = false
}

variable "nat_gateway_count" {
  description = "Number of NAT gateways to create (0 = disabled, 1 = single point of failure, 2+ = HA)"
  type        = number
  default     = 1

  validation {
    condition     = var.nat_gateway_count >= 0 && var.nat_gateway_count <= 3
    error_message = "NAT gateway count must be between 0 and 3"
  }
}

# -----------------------------------------------------------------------------
# Common Tags
# -----------------------------------------------------------------------------

variable "tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}
