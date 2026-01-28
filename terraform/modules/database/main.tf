# =============================================================================
# Database Module - RDS PostgreSQL
# =============================================================================
# Purpose: Provision RDS PostgreSQL for Airflow metadata and data warehouse
# This module demonstrates RDS configuration with security best practices
# In production, this would include read replicas, enhanced monitoring,
# and integration with AWS Secrets Manager for credential management
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

# -----------------------------------------------------------------------------
# DB Subnet Group
# -----------------------------------------------------------------------------
# RDS instances must be deployed in a DB subnet group
# Requires at least 2 subnets in different availability zones

resource "aws_db_subnet_group" "postgres" {
  name       = "${var.project_name}-${var.environment}-db-subnet"
  subnet_ids = var.subnet_ids

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-${var.environment}-db-subnet-group"
      Description = "Subnet group for RDS PostgreSQL instance"
    }
  )
}

# -----------------------------------------------------------------------------
# DB Parameter Group
# -----------------------------------------------------------------------------
# Custom parameter group for PostgreSQL optimization
# Production would include performance tuning parameters based on workload

resource "aws_db_parameter_group" "postgres" {
  name   = "${var.project_name}-${var.environment}-postgres15"
  family = "postgres15"

  description = "Custom parameter group for ${var.environment} PostgreSQL"

  # Example parameters - production would be tuned based on workload
  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_duration"
    value = "1"
  }

  # Adjust work_mem based on environment (more for prod)
  parameter {
    name  = "work_mem"
    value = var.work_mem_kb
  }

  tags = var.tags
}

# -----------------------------------------------------------------------------
# RDS PostgreSQL Instance
# -----------------------------------------------------------------------------
# Main database instance for Airflow metadata and data warehouse
# Dev: Small instance, single-AZ for cost savings
# Prod: Larger instance, multi-AZ for high availability

resource "aws_db_instance" "postgres" {
  identifier = "${var.project_name}-${var.environment}-postgres"

  # Engine configuration
  engine            = "postgres"
  engine_version    = var.engine_version
  instance_class    = var.instance_class
  allocated_storage = var.allocated_storage
  storage_type      = var.storage_type
  storage_encrypted = true

  # Database configuration
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password # Production: Use AWS Secrets Manager

  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.postgres.name
  vpc_security_group_ids = var.security_group_ids
  publicly_accessible    = false # Never expose database publicly

  # High availability and backup
  multi_az                = var.multi_az
  backup_retention_period = var.backup_retention_days
  backup_window           = var.backup_window
  maintenance_window      = var.maintenance_window

  # Snapshot and deletion protection
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = "${var.project_name}-${var.environment}-final-snapshot-${formatdate("YYYY-MM-DD-hhmm", timestamp())}"
  deletion_protection       = var.deletion_protection

  # Parameter and option groups
  parameter_group_name = aws_db_parameter_group.postgres.name

  # Monitoring
  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  monitoring_interval             = var.enhanced_monitoring_interval
  monitoring_role_arn             = var.enhanced_monitoring_interval > 0 ? var.monitoring_role_arn : null

  # Performance insights (prod only, additional cost)
  performance_insights_enabled          = var.enable_performance_insights
  performance_insights_retention_period = var.enable_performance_insights ? 7 : null

  # Auto minor version upgrades during maintenance window
  auto_minor_version_upgrade = true

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-${var.environment}-postgres"
      Description = "PostgreSQL database for Airflow metadata and data warehouse"
    }
  )

  lifecycle {
    # Prevent accidental deletion of database
    prevent_destroy = false # Set to true in production

    # Ignore password changes (managed externally via Secrets Manager in prod)
    ignore_changes = [password]
  }
}

# -----------------------------------------------------------------------------
# CloudWatch Alarms (Optional - Commented Out)
# -----------------------------------------------------------------------------
# Production would include alarms for:
# - High CPU utilization
# - Low free storage space
# - High database connections
# - Replication lag (if using read replicas)
#
# Example (not implemented to keep module simple):
# resource "aws_cloudwatch_metric_alarm" "database_cpu" {
#   alarm_name          = "${var.project_name}-${var.environment}-db-cpu"
#   comparison_operator = "GreaterThanThreshold"
#   evaluation_periods  = "2"
#   metric_name         = "CPUUtilization"
#   namespace           = "AWS/RDS"
#   period              = "300"
#   statistic           = "Average"
#   threshold           = "80"
#   alarm_description   = "Database CPU utilization is too high"
#   dimensions = {
#     DBInstanceIdentifier = aws_db_instance.postgres.id
#   }
# }
