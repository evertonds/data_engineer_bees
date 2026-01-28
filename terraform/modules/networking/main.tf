# =============================================================================
# Networking Module - VPC and Network Infrastructure
# =============================================================================
# Purpose: Create VPC, subnets, security groups, and network routing
# This module demonstrates AWS networking best practices
# In production, this would include VPC endpoints, flow logs, and
# more granular security group rules
# =============================================================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Get available availability zones
data "aws_availability_zones" "available" {
  state = "available"
}

# -----------------------------------------------------------------------------
# VPC
# -----------------------------------------------------------------------------
# Main VPC for all resources
# Enables DNS hostnames for RDS and other services

resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-${var.environment}-vpc"
      Description = "Main VPC for BEES data platform"
    }
  )
}

# -----------------------------------------------------------------------------
# Internet Gateway
# -----------------------------------------------------------------------------
# Required for public subnet internet access

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-igw"
    }
  )
}

# -----------------------------------------------------------------------------
# Public Subnets
# -----------------------------------------------------------------------------
# MWAA requires public subnets for webserver access
# NAT gateways are placed in public subnets

resource "aws_subnet" "public" {
  count = var.public_subnet_count

  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-public-${count.index + 1}"
      Type = "public"
    }
  )
}

# -----------------------------------------------------------------------------
# Private Subnets
# -----------------------------------------------------------------------------
# RDS and MWAA workers run in private subnets
# Access internet via NAT gateway (prod) or no internet (dev)

resource "aws_subnet" "private" {
  count = var.private_subnet_count

  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + var.public_subnet_count)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-private-${count.index + 1}"
      Type = "private"
    }
  )
}

# -----------------------------------------------------------------------------
# NAT Gateway (Production Only)
# -----------------------------------------------------------------------------
# Allows private subnet resources to access internet for package downloads
# Note: NAT Gateway has significant cost (~$30-45/month)
# Dev environment skips NAT gateway for cost savings

resource "aws_eip" "nat" {
  count = var.enable_nat_gateway ? var.nat_gateway_count : 0

  domain = "vpc"

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-nat-eip-${count.index + 1}"
    }
  )

  depends_on = [aws_internet_gateway.main]
}

resource "aws_nat_gateway" "main" {
  count = var.enable_nat_gateway ? var.nat_gateway_count : 0

  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-nat-${count.index + 1}"
    }
  )

  depends_on = [aws_internet_gateway.main]
}

# -----------------------------------------------------------------------------
# Route Tables
# -----------------------------------------------------------------------------

# Public route table - routes to internet gateway
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-public-rt"
      Type = "public"
    }
  )
}

# Associate public subnets with public route table
resource "aws_route_table_association" "public" {
  count = var.public_subnet_count

  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Private route tables - routes to NAT gateway (if enabled)
resource "aws_route_table" "private" {
  count = var.private_subnet_count

  vpc_id = aws_vpc.main.id

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-private-rt-${count.index + 1}"
      Type = "private"
    }
  )
}

# Add route to NAT gateway if enabled (production only)
resource "aws_route" "private_nat" {
  count = var.enable_nat_gateway ? var.private_subnet_count : 0

  route_table_id         = aws_route_table.private[count.index].id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.main[count.index % var.nat_gateway_count].id
}

# Associate private subnets with private route tables
resource "aws_route_table_association" "private" {
  count = var.private_subnet_count

  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private[count.index].id
}

# -----------------------------------------------------------------------------
# Security Groups
# -----------------------------------------------------------------------------

# MWAA Security Group
resource "aws_security_group" "mwaa" {
  name        = "${var.project_name}-${var.environment}-mwaa-sg"
  description = "Security group for MWAA environment"
  vpc_id      = aws_vpc.main.id

  # Allow all outbound traffic
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  # Self-referencing rule for internal MWAA communication
  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    self        = true
    description = "Allow internal MWAA communication"
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-mwaa-sg"
    }
  )
}

# RDS Security Group
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-${var.environment}-rds-sg"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = aws_vpc.main.id

  # Allow PostgreSQL access from MWAA security group
  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.mwaa.id]
    description     = "Allow PostgreSQL access from MWAA"
  }

  # Allow outbound traffic (for replication, backups, etc.)
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-${var.environment}-rds-sg"
    }
  )
}

# -----------------------------------------------------------------------------
# VPC Endpoints (Optional - Commented Out)
# -----------------------------------------------------------------------------
# Production would include VPC endpoints for:
# - S3 (gateway endpoint - no cost)
# - CloudWatch Logs (interface endpoint)
# - Secrets Manager (interface endpoint)
# These reduce data transfer costs and improve security
#
# Example (not implemented to keep module simple):
# resource "aws_vpc_endpoint" "s3" {
#   vpc_id       = aws_vpc.main.id
#   service_name = "com.amazonaws.${var.aws_region}.s3"
#   route_table_ids = concat(
#     [aws_route_table.public.id],
#     aws_route_table.private[*].id
#   )
# }
