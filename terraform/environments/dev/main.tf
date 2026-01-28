# =============================================================================
# Development Environment Configuration
# =============================================================================
# Purpose: Minimal cost development environment for BEES data platform
#
# Characteristics:
# - Single-AZ deployment (cost savings)
# - Small instance sizes (db.t3.micro, mw1.small)
# - No NAT gateway (cost savings, limited internet access)
# - Shorter retention periods
# - Minimal worker count
#
# Estimated Monthly Cost: ~$150-200
# - RDS: ~$15 (db.t3.micro)
# - MWAA: ~$100-120 (mw1.small with 1 worker)
# - S3: ~$5 (minimal storage)
# - Data transfer: ~$10
# =============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Backend configuration - uncomment and configure for remote state
  # See ../backend.tf.example for S3 backend setup
  # backend "s3" {
  #   bucket         = "bees-breweries-terraform-state"
  #   key            = "env/dev/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-state-lock"
  # }
}

# -----------------------------------------------------------------------------
# Provider Configuration
# -----------------------------------------------------------------------------

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      CostCenter  = "Development"
    }
  }
}

# -----------------------------------------------------------------------------
# Local Variables
# -----------------------------------------------------------------------------

locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# -----------------------------------------------------------------------------
# Networking Module
# -----------------------------------------------------------------------------
# Creates VPC, subnets, security groups
# Dev: No NAT gateway to save costs (~$30-45/month savings)

module "networking" {
  source = "../../modules/networking"

  project_name = var.project_name
  environment  = var.environment

  vpc_cidr             = var.vpc_cidr
  public_subnet_count  = 2 # Required minimum for MWAA
  private_subnet_count = 2 # Required minimum for RDS Multi-AZ

  # Cost optimization: Disable NAT gateway in dev
  # Note: This means private subnets cannot access internet
  # MWAA can still function but cannot install external packages
  enable_nat_gateway = false
  nat_gateway_count  = 0

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# IAM Module
# -----------------------------------------------------------------------------
# Creates IAM roles and policies for MWAA and RDS

module "iam" {
  source = "../../modules/iam"

  project_name = var.project_name
  environment  = var.environment

  # S3 bucket ARNs from storage module
  airflow_bucket_arn = module.storage.airflow_bucket_arn
  data_bucket_arns   = module.storage.all_bucket_arns

  # Feature flags
  enable_rds_access             = true
  enable_secrets_manager_access = false # Not using Secrets Manager in dev
  create_rds_monitoring_role    = false # No enhanced monitoring in dev

  tags = local.common_tags

  depends_on = [module.storage]
}

# -----------------------------------------------------------------------------
# Storage Module
# -----------------------------------------------------------------------------
# Creates S3 buckets for medallion architecture (bronze, silver, gold)

module "storage" {
  source = "../../modules/storage"

  project_name = var.project_name
  environment  = var.environment

  enable_versioning      = true  # Keep versioning for data safety
  enable_lifecycle_rules = false # Disable lifecycle rules in dev (keep costs simple)

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Database Module
# -----------------------------------------------------------------------------
# Creates RDS PostgreSQL for Airflow metadata and data warehouse
# Dev: Minimal configuration for cost savings

module "database" {
  source = "../../modules/database"

  project_name = var.project_name
  environment  = var.environment

  # Instance configuration - smallest available
  instance_class    = "db.t3.micro" # 2 vCPU, 1 GB RAM
  allocated_storage = 20            # Minimum allowed
  storage_type      = "gp3"         # Latest generation

  # Database configuration
  db_name     = var.db_name
  db_username = var.db_username
  db_password = var.db_password # Production: Use AWS Secrets Manager

  # Network configuration
  subnet_ids         = module.networking.database_subnet_ids
  security_group_ids = module.networking.database_security_group_ids

  # High availability - disabled for cost savings
  multi_az              = false # Single-AZ only
  backup_retention_days = 1     # Minimal backup retention
  backup_window         = "03:00-04:00"
  maintenance_window    = "sun:04:00-sun:05:00"
  skip_final_snapshot   = true  # Skip final snapshot on destroy
  deletion_protection   = false # Allow deletion without extra steps

  # Monitoring - disabled for cost savings
  enhanced_monitoring_interval = 0     # No enhanced monitoring
  enable_performance_insights  = false # No Performance Insights

  # Performance tuning
  work_mem_kb = "4096" # 4 MB

  tags = local.common_tags

  depends_on = [module.networking]
}

# -----------------------------------------------------------------------------
# Airflow Module
# -----------------------------------------------------------------------------
# Creates AWS MWAA environment
# Dev: Minimal environment for development and testing

module "airflow" {
  source = "../../modules/airflow"

  project_name   = var.project_name
  environment    = var.environment
  aws_account_id = data.aws_caller_identity.current.account_id

  # S3 bucket for DAGs (created in storage module)
  airflow_bucket_name = module.storage.airflow_bucket_name
  airflow_bucket_arn  = module.storage.airflow_bucket_arn

  # Environment configuration
  airflow_version   = "2.7.2"
  environment_class = "mw1.small" # Smallest available: 1 worker, 1.5 vCPU, 2 GB RAM

  # Worker scaling - minimal for dev
  min_workers      = 1 # Single worker
  max_workers      = 1 # No auto-scaling
  schedulers_count = 2 # Minimum allowed

  # Network configuration
  subnet_ids            = module.networking.mwaa_subnet_ids
  security_group_ids    = module.networking.mwaa_security_group_ids
  execution_role_arn    = module.iam.mwaa_execution_role_arn
  webserver_access_mode = "PUBLIC_ONLY" # Allow access from anywhere (with authentication)

  # Logging configuration - shorter retention for dev
  log_retention_days       = 3 # 3 days only
  dag_processing_log_level = "INFO"
  scheduler_log_level      = "INFO"
  task_log_level           = "INFO"
  webserver_log_level      = "INFO"
  worker_log_level         = "INFO"

  # Airflow configuration
  dag_concurrency         = 8  # Lower concurrency
  parallelism             = 16 # Lower parallelism
  max_active_runs_per_dag = 1  # One run at a time

  # Maintenance window
  maintenance_window = "SUN:03:00"

  tags = local.common_tags

  depends_on = [module.networking, module.iam]
}

# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

data "aws_caller_identity" "current" {}
