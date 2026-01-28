# =============================================================================
# Storage Module - Outputs
# =============================================================================
# These outputs are consumed by other modules (e.g., Airflow needs bucket names)
# and displayed after terraform apply for manual configuration steps

# -----------------------------------------------------------------------------
# Bronze Layer Outputs
# -----------------------------------------------------------------------------

output "bronze_bucket_name" {
  description = "Name of the bronze layer S3 bucket (raw data)"
  value       = aws_s3_bucket.bronze.id
}

output "bronze_bucket_arn" {
  description = "ARN of the bronze layer S3 bucket for IAM policy configuration"
  value       = aws_s3_bucket.bronze.arn
}

output "bronze_bucket_region" {
  description = "AWS region where bronze bucket is deployed"
  value       = aws_s3_bucket.bronze.region
}

# -----------------------------------------------------------------------------
# Silver Layer Outputs
# -----------------------------------------------------------------------------

output "silver_bucket_name" {
  description = "Name of the silver layer S3 bucket (cleaned data)"
  value       = aws_s3_bucket.silver.id
}

output "silver_bucket_arn" {
  description = "ARN of the silver layer S3 bucket for IAM policy configuration"
  value       = aws_s3_bucket.silver.arn
}

output "silver_bucket_region" {
  description = "AWS region where silver bucket is deployed"
  value       = aws_s3_bucket.silver.region
}

# -----------------------------------------------------------------------------
# Gold Layer Outputs
# -----------------------------------------------------------------------------

output "gold_bucket_name" {
  description = "Name of the gold layer S3 bucket (analytics-ready data)"
  value       = aws_s3_bucket.gold.id
}

output "gold_bucket_arn" {
  description = "ARN of the gold layer S3 bucket for IAM policy configuration"
  value       = aws_s3_bucket.gold.arn
}

output "gold_bucket_region" {
  description = "AWS region where gold bucket is deployed"
  value       = aws_s3_bucket.gold.region
}

# -----------------------------------------------------------------------------
# Airflow Bucket Outputs
# -----------------------------------------------------------------------------

output "airflow_bucket_name" {
  description = "Name of the Airflow DAGs S3 bucket"
  value       = aws_s3_bucket.airflow.id
}

output "airflow_bucket_arn" {
  description = "ARN of the Airflow DAGs S3 bucket for IAM policy configuration"
  value       = aws_s3_bucket.airflow.arn
}

# -----------------------------------------------------------------------------
# Aggregated Outputs
# -----------------------------------------------------------------------------

output "all_bucket_names" {
  description = "List of all bucket names for reference"
  value = [
    aws_s3_bucket.bronze.id,
    aws_s3_bucket.silver.id,
    aws_s3_bucket.gold.id,
  ]
}

output "all_bucket_arns" {
  description = "List of all bucket ARNs for IAM policy configuration"
  value = [
    aws_s3_bucket.bronze.arn,
    aws_s3_bucket.silver.arn,
    aws_s3_bucket.gold.arn,
  ]
}
