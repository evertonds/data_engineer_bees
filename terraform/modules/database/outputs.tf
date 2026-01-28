# =============================================================================
# Database Module - Outputs
# =============================================================================
# These outputs provide connection information for Airflow and other services

# -----------------------------------------------------------------------------
# Connection Information
# -----------------------------------------------------------------------------

output "db_instance_id" {
  description = "RDS instance identifier"
  value       = aws_db_instance.postgres.id
}

output "db_instance_arn" {
  description = "ARN of the RDS instance"
  value       = aws_db_instance.postgres.arn
}

output "db_endpoint" {
  description = "Connection endpoint (hostname:port)"
  value       = aws_db_instance.postgres.endpoint
}

output "db_address" {
  description = "Hostname of the RDS instance"
  value       = aws_db_instance.postgres.address
}

output "db_port" {
  description = "Port number for database connections"
  value       = aws_db_instance.postgres.port
}

output "db_name" {
  description = "Name of the default database"
  value       = aws_db_instance.postgres.db_name
}

output "db_username" {
  description = "Master username for database access"
  value       = aws_db_instance.postgres.username
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Connection String
# -----------------------------------------------------------------------------

output "connection_string" {
  description = "PostgreSQL connection string (password not included)"
  value       = "postgresql://${aws_db_instance.postgres.username}@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${aws_db_instance.postgres.db_name}"
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Configuration Information
# -----------------------------------------------------------------------------

output "db_engine_version" {
  description = "PostgreSQL engine version"
  value       = aws_db_instance.postgres.engine_version_actual
}

output "db_instance_class" {
  description = "RDS instance class"
  value       = aws_db_instance.postgres.instance_class
}

output "db_allocated_storage" {
  description = "Allocated storage in GB"
  value       = aws_db_instance.postgres.allocated_storage
}

output "db_multi_az" {
  description = "Whether Multi-AZ is enabled"
  value       = aws_db_instance.postgres.multi_az
}

output "db_availability_zone" {
  description = "Availability zone of the RDS instance"
  value       = aws_db_instance.postgres.availability_zone
}

# -----------------------------------------------------------------------------
# Monitoring and Backup Information
# -----------------------------------------------------------------------------

output "db_backup_retention_period" {
  description = "Backup retention period in days"
  value       = aws_db_instance.postgres.backup_retention_period
}

output "db_monitoring_enabled" {
  description = "Whether enhanced monitoring is enabled"
  value       = aws_db_instance.postgres.monitoring_interval > 0
}

output "db_performance_insights_enabled" {
  description = "Whether Performance Insights is enabled"
  value       = aws_db_instance.postgres.performance_insights_enabled
}

# -----------------------------------------------------------------------------
# Resource References
# -----------------------------------------------------------------------------

output "db_subnet_group_name" {
  description = "Name of the DB subnet group"
  value       = aws_db_subnet_group.postgres.name
}

output "db_parameter_group_name" {
  description = "Name of the DB parameter group"
  value       = aws_db_parameter_group.postgres.name
}
