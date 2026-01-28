# =============================================================================
# Airflow Module - Outputs
# =============================================================================

# -----------------------------------------------------------------------------
# MWAA Environment Information
# -----------------------------------------------------------------------------

output "mwaa_environment_name" {
  description = "Name of the MWAA environment"
  value       = aws_mwaa_environment.airflow.name
}

output "mwaa_environment_arn" {
  description = "ARN of the MWAA environment"
  value       = aws_mwaa_environment.airflow.arn
}

output "mwaa_webserver_url" {
  description = "URL of the Airflow webserver UI"
  value       = aws_mwaa_environment.airflow.webserver_url
}

output "mwaa_service_role_arn" {
  description = "IAM service role ARN used by MWAA"
  value       = aws_mwaa_environment.airflow.service_role_arn
}

output "mwaa_status" {
  description = "Status of the MWAA environment"
  value       = aws_mwaa_environment.airflow.status
}

# -----------------------------------------------------------------------------
# S3 Bucket Information
# -----------------------------------------------------------------------------

output "airflow_bucket_name" {
  description = "Name of the S3 bucket storing DAGs and plugins"
  value       = var.airflow_bucket_name
}

output "airflow_bucket_arn" {
  description = "ARN of the S3 bucket storing DAGs and plugins"
  value       = var.airflow_bucket_arn
}

output "dag_s3_path" {
  description = "S3 path where DAGs should be uploaded"
  value       = "s3://${var.airflow_bucket_name}/dags/"
}

# -----------------------------------------------------------------------------
# CloudWatch Log Groups
# -----------------------------------------------------------------------------

output "log_group_dag_processing" {
  description = "CloudWatch log group for DAG processing logs"
  value       = aws_cloudwatch_log_group.airflow_dag_processing.name
}

output "log_group_scheduler" {
  description = "CloudWatch log group for scheduler logs"
  value       = aws_cloudwatch_log_group.airflow_scheduler.name
}

output "log_group_webserver" {
  description = "CloudWatch log group for webserver logs"
  value       = aws_cloudwatch_log_group.airflow_webserver.name
}

output "log_group_worker" {
  description = "CloudWatch log group for worker logs"
  value       = aws_cloudwatch_log_group.airflow_worker.name
}

output "log_group_task" {
  description = "CloudWatch log group for task logs"
  value       = aws_cloudwatch_log_group.airflow_task.name
}

# -----------------------------------------------------------------------------
# Configuration Information
# -----------------------------------------------------------------------------

output "airflow_version" {
  description = "Apache Airflow version deployed"
  value       = aws_mwaa_environment.airflow.airflow_version
}

output "environment_class" {
  description = "MWAA environment class (compute size)"
  value       = aws_mwaa_environment.airflow.environment_class
}

output "min_workers" {
  description = "Minimum number of workers configured"
  value       = aws_mwaa_environment.airflow.min_workers
}

output "max_workers" {
  description = "Maximum number of workers configured"
  value       = aws_mwaa_environment.airflow.max_workers
}

output "webserver_access_mode" {
  description = "Webserver access mode (PUBLIC_ONLY or PRIVATE_ONLY)"
  value       = aws_mwaa_environment.airflow.webserver_access_mode
}

# -----------------------------------------------------------------------------
# Quick Reference Commands
# -----------------------------------------------------------------------------

output "dag_upload_command" {
  description = "AWS CLI command to upload DAGs to S3"
  value       = "aws s3 sync ./dags s3://${var.airflow_bucket_name}/dags/ --delete"
}

output "webserver_login_command" {
  description = "AWS CLI command to get webserver login token"
  value       = "aws mwaa create-web-login-token --name ${aws_mwaa_environment.airflow.name}"
}
