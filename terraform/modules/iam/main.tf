# =============================================================================
# IAM Module - Roles and Policies
# =============================================================================
# Purpose: Create IAM roles and policies for MWAA and other services
# This module demonstrates least-privilege access patterns
# In production, this would include more granular policies,
# service control policies, and integration with AWS Organizations
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

# Get current AWS account ID and region
data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# -----------------------------------------------------------------------------
# MWAA Execution Role
# -----------------------------------------------------------------------------
# This role is assumed by MWAA to execute Airflow tasks
# Needs permissions for S3, CloudWatch Logs, and other AWS services

resource "aws_iam_role" "mwaa_execution" {
  name        = "${var.project_name}-${var.environment}-mwaa-execution"
  description = "Execution role for MWAA environment"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = [
            "airflow.amazonaws.com",
            "airflow-env.amazonaws.com"
          ]
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-${var.environment}-mwaa-execution"
      Description = "MWAA execution role"
    }
  )
}

# -----------------------------------------------------------------------------
# S3 Access Policy for MWAA
# -----------------------------------------------------------------------------
# Allow MWAA to read DAGs and access data lake buckets

resource "aws_iam_role_policy" "mwaa_s3_access" {
  name = "s3-access"
  role = aws_iam_role.mwaa_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject*",
          "s3:GetBucket*",
          "s3:List*"
        ]
        Resource = [
          var.airflow_bucket_arn,
          "${var.airflow_bucket_arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject*",
          "s3:PutObject*",
          "s3:DeleteObject*",
          "s3:List*"
        ]
        Resource = flatten([
          for arn in var.data_bucket_arns : [
            arn,
            "${arn}/*"
          ]
        ])
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# CloudWatch Logs Policy for MWAA
# -----------------------------------------------------------------------------
# Allow MWAA to write logs to CloudWatch

resource "aws_iam_role_policy" "mwaa_cloudwatch_logs" {
  name = "cloudwatch-logs"
  role = aws_iam_role.mwaa_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:CreateLogGroup",
          "logs:PutLogEvents",
          "logs:GetLogEvents",
          "logs:GetLogRecord",
          "logs:GetLogGroupFields",
          "logs:GetQueryResults"
        ]
        Resource = "arn:aws:logs:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:log-group:/aws/mwaa/${var.project_name}-${var.environment}*"
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# MWAA Service Policy
# -----------------------------------------------------------------------------
# Base policy for MWAA operations

resource "aws_iam_role_policy" "mwaa_base" {
  name = "mwaa-base"
  role = aws_iam_role.mwaa_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "airflow:PublishMetrics"
        ]
        Resource = "arn:aws:airflow:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:environment/${var.project_name}-${var.environment}"
      },
      {
        Effect = "Allow"
        Action = [
          "sqs:ChangeMessageVisibility",
          "sqs:DeleteMessage",
          "sqs:GetQueueAttributes",
          "sqs:GetQueueUrl",
          "sqs:ReceiveMessage",
          "sqs:SendMessage"
        ]
        Resource = "arn:aws:sqs:${data.aws_region.current.name}:*:airflow-celery-*"
      },
      {
        Effect = "Allow"
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:GenerateDataKey*",
          "kms:Encrypt"
        ]
        NotResource = "arn:aws:kms:*:${data.aws_caller_identity.current.account_id}:key/*"
        Condition = {
          StringLike = {
            "kms:ViaService" = [
              "sqs.${data.aws_region.current.name}.amazonaws.com",
              "s3.${data.aws_region.current.name}.amazonaws.com"
            ]
          }
        }
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# RDS Access Policy (Optional)
# -----------------------------------------------------------------------------
# If using RDS for data warehouse, MWAA tasks may need to connect
# Production should use IAM database authentication or Secrets Manager

resource "aws_iam_role_policy" "mwaa_rds_access" {
  count = var.enable_rds_access ? 1 : 0

  name = "rds-access"
  role = aws_iam_role.mwaa_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds:DescribeDBInstances",
          "rds:DescribeDBClusters"
        ]
        Resource = "*"
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# Secrets Manager Policy (Production Use)
# -----------------------------------------------------------------------------
# For retrieving database passwords and API keys
# Note: This is a placeholder - actual secrets would be created separately

resource "aws_iam_role_policy" "mwaa_secrets_manager" {
  count = var.enable_secrets_manager_access ? 1 : 0

  name = "secrets-manager"
  role = aws_iam_role.mwaa_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = "arn:aws:secretsmanager:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:secret:${var.project_name}/${var.environment}/*"
      }
    ]
  })
}

# -----------------------------------------------------------------------------
# RDS Enhanced Monitoring Role (Optional)
# -----------------------------------------------------------------------------
# Separate role for RDS enhanced monitoring
# Only needed if enhanced monitoring is enabled on RDS

resource "aws_iam_role" "rds_monitoring" {
  count = var.create_rds_monitoring_role ? 1 : 0

  name        = "${var.project_name}-${var.environment}-rds-monitoring"
  description = "IAM role for RDS enhanced monitoring"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  count = var.create_rds_monitoring_role ? 1 : 0

  role       = aws_iam_role.rds_monitoring[0].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# -----------------------------------------------------------------------------
# Additional Custom Policies (Placeholder)
# -----------------------------------------------------------------------------
# Production would include:
# - Policy for AWS Glue Data Catalog access (if using)
# - Policy for Step Functions (if orchestrating across services)
# - Policy for SNS/SQS (if using for notifications)
# - Policy for Lambda invocation (if using serverless components)
#
# Example (not implemented):
# resource "aws_iam_role_policy" "mwaa_glue" {
#   name = "glue-access"
#   role = aws_iam_role.mwaa_execution.id
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [{
#       Effect = "Allow"
#       Action = [
#         "glue:GetDatabase",
#         "glue:GetTable",
#         "glue:GetPartitions"
#       ]
#       Resource = "*"
#     }]
#   })
# }
