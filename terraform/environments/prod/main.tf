# =============================================================================
# Production Environment Configuration
# =============================================================================
# Purpose: Production-ready environment with high availability and performance
#
# Characteristics:
# - Multi-AZ deployment (high availability)
# - Larger instance sizes (db.t3.medium, mw1.medium)
# - NAT gateway enabled (private subnet internet access)
# - Longer retention periods
# - Auto-scaling workers
# - Enhanced monitoring and backups
#
# Estimated Monthly Cost: ~$500-700
# - RDS: ~$100 (db.t3.medium Multi-AZ)
# - MWAA: ~$350-450 (mw1.medium with 2-5 workers)
# - NAT Gateway: ~$35 (data transfer + hourly)
# - S3: ~$20 (more storage, versioning)
# - CloudWatch: ~$10
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
  #   key            = "env/prod/terraform.tfstate"
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
      CostCenter  = "Production"
      Compliance  = "Required"
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
# Prod: NAT gateway enabled for private subnet internet access

module "networking" {
  source = "../../modules/networking"

  project_name = var.project_name
  environment  = var.environment

  vpc_cidr             = var.vpc_cidr
  public_subnet_count  = 2 # Required minimum for MWAA
  private_subnet_count = 2 # Required minimum for RDS Multi-AZ

  # Enable NAT gateway for production
  # Allows private subnets to access internet for package downloads
  # Cost: ~$32/month + data transfer charges
  enable_nat_gateway = true
  nat_gateway_count  = 1 # Single NAT gateway (use 2 for full HA)

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
  enable_secrets_manager_access = true # Use Secrets Manager in prod
  create_rds_monitoring_role    = true # Enable enhanced monitoring

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

  enable_versioning      = true # Required for production
  enable_lifecycle_rules = true # Cost optimization through tiering

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Database Module
# -----------------------------------------------------------------------------
# Creates RDS PostgreSQL for Airflow metadata and data warehouse
# Prod: High availability and performance configuration

module "database" {
  source = "../../modules/database"

  project_name = var.project_name
  environment  = var.environment

  # Instance configuration - production sizing
  instance_class    = "db.t3.medium" # 2 vCPU, 4 GB RAM
  allocated_storage = 100            # 100 GB
  storage_type      = "gp3"          # Latest generation

  # Database configuration
  db_name     = var.db_name
  db_username = var.db_username
  db_password = var.db_password # Production: Use AWS Secrets Manager

  # Network configuration
  subnet_ids         = module.networking.database_subnet_ids
  security_group_ids = module.networking.database_security_group_ids

  # High availability - enabled for production
  multi_az              = true # Multi-AZ for HA
  backup_retention_days = 7    # 7 days backup retention
  backup_window         = "03:00-04:00"
  maintenance_window    = "sun:04:00-sun:05:00"
  skip_final_snapshot   = false # Create final snapshot
  deletion_protection   = true  # Prevent accidental deletion

  # Monitoring - enabled for production
  enhanced_monitoring_interval = 60 # Enhanced monitoring every 60 seconds
  monitoring_role_arn          = module.iam.rds_monitoring_role_arn
  enable_performance_insights  = true # Enable Performance Insights

  # Performance tuning - higher for production
  work_mem_kb = "8192" # 8 MB

  tags = local.common_tags

  depends_on = [module.networking, module.iam]
}

# -----------------------------------------------------------------------------
# Airflow Module
# -----------------------------------------------------------------------------
# Creates AWS MWAA environment
# Prod: Scaled environment with auto-scaling workers

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
  environment_class = "mw1.medium" # Medium: 2 vCPU, 4 GB RAM per worker

  # Worker scaling - auto-scaling for production
  min_workers      = 2 # Minimum 2 workers
  max_workers      = 5 # Auto-scale up to 5 workers
  schedulers_count = 2 # Multiple schedulers for reliability

  # Network configuration
  subnet_ids            = module.networking.mwaa_subnet_ids
  security_group_ids    = module.networking.mwaa_security_group_ids
  execution_role_arn    = module.iam.mwaa_execution_role_arn
  webserver_access_mode = "PUBLIC_ONLY" # Could use PRIVATE_ONLY with VPN

  # Logging configuration - longer retention for production
  log_retention_days       = 30 # 30 days retention
  dag_processing_log_level = "INFO"
  scheduler_log_level      = "INFO"
  task_log_level           = "INFO"
  webserver_log_level      = "WARNING"
  worker_log_level         = "INFO"

  # Airflow configuration - higher concurrency for production
  dag_concurrency         = 16 # Higher concurrency
  parallelism             = 32 # Higher parallelism
  max_active_runs_per_dag = 3  # Multiple concurrent runs

  # Maintenance window
  maintenance_window = "SUN:03:00"

  tags = local.common_tags

  depends_on = [module.networking, module.iam]
}

# -----------------------------------------------------------------------------
# Data Sources
# -----------------------------------------------------------------------------

data "aws_caller_identity" "current" {}
