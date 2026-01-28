# =============================================================================
# Development Environment - Outputs
# =============================================================================
# These outputs provide key information after deployment

# -----------------------------------------------------------------------------
# Networking Outputs
# -----------------------------------------------------------------------------

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.networking.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.networking.public_subnet_ids
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = module.networking.private_subnet_ids
}

# -----------------------------------------------------------------------------
# Storage Outputs
# -----------------------------------------------------------------------------

output "bronze_bucket" {
  description = "Bronze layer S3 bucket name"
  value       = module.storage.bronze_bucket_name
}

output "silver_bucket" {
  description = "Silver layer S3 bucket name"
  value       = module.storage.silver_bucket_name
}

output "gold_bucket" {
  description = "Gold layer S3 bucket name"
  value       = module.storage.gold_bucket_name
}

output "airflow_bucket" {
  description = "Airflow DAGs S3 bucket name"
  value       = module.airflow.airflow_bucket_name
}

# -----------------------------------------------------------------------------
# Database Outputs
# -----------------------------------------------------------------------------

output "database_endpoint" {
  description = "RDS PostgreSQL connection endpoint"
  value       = module.database.db_endpoint
}

output "database_name" {
  description = "Database name"
  value       = module.database.db_name
}

output "database_connection_string" {
  description = "PostgreSQL connection string (without password)"
  value       = module.database.connection_string
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Airflow Outputs
# -----------------------------------------------------------------------------

output "airflow_webserver_url" {
  description = "URL to access Airflow web UI"
  value       = module.airflow.mwaa_webserver_url
}

output "airflow_environment_name" {
  description = "MWAA environment name"
  value       = module.airflow.mwaa_environment_name
}

output "airflow_version" {
  description = "Apache Airflow version"
  value       = module.airflow.airflow_version
}

# -----------------------------------------------------------------------------
# IAM Outputs
# -----------------------------------------------------------------------------

output "mwaa_execution_role_arn" {
  description = "ARN of the MWAA execution role"
  value       = module.iam.mwaa_execution_role_arn
}

# -----------------------------------------------------------------------------
# Quick Start Commands
# -----------------------------------------------------------------------------

output "dag_upload_command" {
  description = "Command to upload DAGs to S3"
  value       = "aws s3 sync ./airflow/dags s3://${module.airflow.airflow_bucket_name}/dags/ --delete"
}

output "database_connection_command" {
  description = "Command to connect to database"
  value       = "psql -h ${module.database.db_address} -U ${module.database.db_username} -d ${module.database.db_name}"
  sensitive   = true
}

# -----------------------------------------------------------------------------
# Environment Summary
# -----------------------------------------------------------------------------

output "environment_summary" {
  description = "Summary of deployed environment"
  value = {
    environment         = var.environment
    region              = var.aws_region
    vpc_id              = module.networking.vpc_id
    nat_gateway_enabled = module.networking.nat_gateway_enabled
    database_class      = module.database.db_instance_class
    database_multi_az   = module.database.db_multi_az
    airflow_class       = module.airflow.environment_class
    airflow_workers     = "${module.airflow.min_workers}-${module.airflow.max_workers}"
  }
}
