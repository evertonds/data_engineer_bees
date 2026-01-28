# =============================================================================
# Networking Module - Outputs
# =============================================================================

# -----------------------------------------------------------------------------
# VPC Outputs
# -----------------------------------------------------------------------------

output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "vpc_cidr" {
  description = "CIDR block of the VPC"
  value       = aws_vpc.main.cidr_block
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = aws_internet_gateway.main.id
}

# -----------------------------------------------------------------------------
# Subnet Outputs
# -----------------------------------------------------------------------------

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "public_subnet_cidrs" {
  description = "List of public subnet CIDR blocks"
  value       = aws_subnet.public[*].cidr_block
}

output "private_subnet_cidrs" {
  description = "List of private subnet CIDR blocks"
  value       = aws_subnet.private[*].cidr_block
}

output "availability_zones" {
  description = "List of availability zones used"
  value       = distinct(concat(aws_subnet.public[*].availability_zone, aws_subnet.private[*].availability_zone))
}

# -----------------------------------------------------------------------------
# NAT Gateway Outputs
# -----------------------------------------------------------------------------

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs (empty if NAT gateway disabled)"
  value       = aws_nat_gateway.main[*].id
}

output "nat_gateway_public_ips" {
  description = "List of public IPs for NAT gateways (empty if NAT gateway disabled)"
  value       = aws_eip.nat[*].public_ip
}

output "nat_gateway_enabled" {
  description = "Whether NAT gateway is enabled"
  value       = var.enable_nat_gateway
}

# -----------------------------------------------------------------------------
# Route Table Outputs
# -----------------------------------------------------------------------------

output "public_route_table_id" {
  description = "ID of the public route table"
  value       = aws_route_table.public.id
}

output "private_route_table_ids" {
  description = "List of private route table IDs"
  value       = aws_route_table.private[*].id
}

# -----------------------------------------------------------------------------
# Security Group Outputs
# -----------------------------------------------------------------------------

output "mwaa_security_group_id" {
  description = "Security group ID for MWAA environment"
  value       = aws_security_group.mwaa.id
}

output "rds_security_group_id" {
  description = "Security group ID for RDS instance"
  value       = aws_security_group.rds.id
}

# -----------------------------------------------------------------------------
# Aggregated Outputs for Other Modules
# -----------------------------------------------------------------------------

output "database_subnet_ids" {
  description = "Subnet IDs for RDS (private subnets)"
  value       = aws_subnet.private[*].id
}

output "mwaa_subnet_ids" {
  description = "Subnet IDs for MWAA (private subnets)"
  value       = aws_subnet.private[*].id
}

output "database_security_group_ids" {
  description = "Security group IDs for RDS"
  value       = [aws_security_group.rds.id]
}

output "mwaa_security_group_ids" {
  description = "Security group IDs for MWAA"
  value       = [aws_security_group.mwaa.id]
}
