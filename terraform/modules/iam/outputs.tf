# =============================================================================
# IAM Module - Outputs
# =============================================================================

# -----------------------------------------------------------------------------
# MWAA Execution Role
# -----------------------------------------------------------------------------

output "mwaa_execution_role_arn" {
  description = "ARN of the MWAA execution role"
  value       = aws_iam_role.mwaa_execution.arn
}

output "mwaa_execution_role_name" {
  description = "Name of the MWAA execution role"
  value       = aws_iam_role.mwaa_execution.name
}

output "mwaa_execution_role_id" {
  description = "ID of the MWAA execution role"
  value       = aws_iam_role.mwaa_execution.id
}

# -----------------------------------------------------------------------------
# RDS Monitoring Role
# -----------------------------------------------------------------------------

output "rds_monitoring_role_arn" {
  description = "ARN of the RDS monitoring role (empty if not created)"
  value       = var.create_rds_monitoring_role ? aws_iam_role.rds_monitoring[0].arn : ""
}

output "rds_monitoring_role_name" {
  description = "Name of the RDS monitoring role (empty if not created)"
  value       = var.create_rds_monitoring_role ? aws_iam_role.rds_monitoring[0].name : ""
}

# -----------------------------------------------------------------------------
# Role Configuration
# -----------------------------------------------------------------------------

output "secrets_manager_enabled" {
  description = "Whether Secrets Manager access is enabled"
  value       = var.enable_secrets_manager_access
}

output "rds_access_enabled" {
  description = "Whether RDS access is enabled"
  value       = var.enable_rds_access
}
