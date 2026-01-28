# =============================================================================
# Airflow Module - AWS MWAA (Managed Workflows for Apache Airflow)
# =============================================================================
# Purpose: Deploy managed Airflow environment on AWS
# This module demonstrates MWAA configuration with appropriate scaling
# In production, this would include custom plugins, requirements.txt,
# VPC endpoints for private access, and integration with CloudWatch
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
# S3 Bucket for DAGs and Plugins
# -----------------------------------------------------------------------------
# MWAA requires an S3 bucket to store DAGs, plugins, and requirements.txt
# The bucket is created in the storage module and passed as a variable
# This avoids circular dependencies between modules

# -----------------------------------------------------------------------------
# CloudWatch Log Groups
# -----------------------------------------------------------------------------
# MWAA sends logs to CloudWatch - separate log groups for different log types

resource "aws_cloudwatch_log_group" "airflow_dag_processing" {
  name              = "/aws/mwaa/${var.project_name}-${var.environment}/dag-processing"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "airflow_scheduler" {
  name              = "/aws/mwaa/${var.project_name}-${var.environment}/scheduler"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "airflow_webserver" {
  name              = "/aws/mwaa/${var.project_name}-${var.environment}/webserver"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "airflow_worker" {
  name              = "/aws/mwaa/${var.project_name}-${var.environment}/worker"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "airflow_task" {
  name              = "/aws/mwaa/${var.project_name}-${var.environment}/task"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

# -----------------------------------------------------------------------------
# MWAA Environment
# -----------------------------------------------------------------------------
# Main Airflow environment - scales based on environment configuration
# Dev: Small environment, minimal workers
# Prod: Medium environment, auto-scaling workers

resource "aws_mwaa_environment" "airflow" {
  name = "${var.project_name}-${var.environment}"

  # Airflow configuration
  airflow_version = var.airflow_version

  # Environment class determines compute resources
  # mw1.small: 1 vCPU, 2 GB RAM per worker (dev)
  # mw1.medium: 2 vCPU, 4 GB RAM per worker (prod)
  # mw1.large: 4 vCPU, 8 GB RAM per worker (heavy workloads)
  environment_class = var.environment_class

  # Worker scaling configuration
  min_workers = var.min_workers
  max_workers = var.max_workers

  # Scheduler configuration
  schedulers = var.schedulers_count

  # DAGs and plugins location
  source_bucket_arn = var.airflow_bucket_arn
  dag_s3_path       = "dags/"

  # Optional: plugins and requirements
  # plugins_s3_path      = "plugins.zip"
  # requirements_s3_path = "requirements.txt"

  # Execution role for Airflow tasks
  execution_role_arn = var.execution_role_arn

  # Network configuration
  # MWAA requires private subnets with NAT gateway for internet access
  network_configuration {
    security_group_ids = var.security_group_ids
    subnet_ids         = var.subnet_ids
  }

  # CloudWatch Logs configuration
  logging_configuration {
    dag_processing_logs {
      enabled   = true
      log_level = var.dag_processing_log_level
    }

    scheduler_logs {
      enabled   = true
      log_level = var.scheduler_log_level
    }

    task_logs {
      enabled   = true
      log_level = var.task_log_level
    }

    webserver_logs {
      enabled   = true
      log_level = var.webserver_log_level
    }

    worker_logs {
      enabled   = true
      log_level = var.worker_log_level
    }
  }

  # Airflow configuration options
  # These map to airflow.cfg settings
  airflow_configuration_options = merge(
    {
      "core.dag_concurrency"               = var.dag_concurrency
      "core.parallelism"                   = var.parallelism
      "core.max_active_runs_per_dag"       = var.max_active_runs_per_dag
      "scheduler.catchup_by_default"       = "False"
      "webserver.warn_deployment_exposure" = "False"
    },
    var.additional_airflow_config
  )

  # Web server access mode
  # PUBLIC_ONLY: Access via public internet (with authentication)
  # PRIVATE_ONLY: Access only within VPC
  webserver_access_mode = var.webserver_access_mode

  # Weekly maintenance window (UTC)
  weekly_maintenance_window_start = var.maintenance_window

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-${var.environment}-mwaa"
      Description = "Managed Airflow environment for data orchestration"
    }
  )

  # Depend on log groups being created first
  depends_on = [
    aws_cloudwatch_log_group.airflow_dag_processing,
    aws_cloudwatch_log_group.airflow_scheduler,
    aws_cloudwatch_log_group.airflow_webserver,
    aws_cloudwatch_log_group.airflow_worker,
    aws_cloudwatch_log_group.airflow_task,
  ]
}

# -----------------------------------------------------------------------------
# S3 Bucket Policy for MWAA Access
# -----------------------------------------------------------------------------
# Allow MWAA to read DAGs and plugins from S3

resource "aws_s3_bucket_policy" "airflow" {
  bucket = var.airflow_bucket_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "airflow.amazonaws.com"
        }
        Action = [
          "s3:GetObject*",
          "s3:GetBucket*",
          "s3:List*"
        ]
        Resource = [
          var.airflow_bucket_arn,
          "${var.airflow_bucket_arn}/*"
        ]
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = var.aws_account_id
          }
        }
      }
    ]
  })
}
