# =============================================================================
# Storage Module - S3 Buckets for Medallion Architecture
# =============================================================================
# Purpose: Create S3 buckets for bronze, silver, and gold data layers
# This module demonstrates data lake structure following medallion architecture
# In production, this would include additional lifecycle policies, replication,
# and more granular access controls
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
# Bronze Layer - Raw Data Storage
# -----------------------------------------------------------------------------
# Stores raw, unprocessed data from source systems
# Retention: Longer (for audit and reprocessing)
# Access: Write by ingestion pipelines, read by transformation jobs

resource "aws_s3_bucket" "bronze" {
  bucket = "${var.project_name}-${var.environment}-bronze"

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-${var.environment}-bronze"
      Layer       = "bronze"
      Description = "Raw data storage - ingestion landing zone"
    }
  )
}

# Enable versioning for data lineage and recovery
# Note: Versioning increases storage costs but provides audit trail
resource "aws_s3_bucket_versioning" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Disabled"
  }
}

# Server-side encryption using S3-managed keys
# Production consideration: Could use KMS for more control and audit
resource "aws_s3_bucket_server_side_encryption_configuration" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Block public access - data lake should never be publicly accessible
resource "aws_s3_bucket_public_access_block" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Lifecycle policy for bronze layer
# Raw data can be transitioned to cheaper storage after initial processing
resource "aws_s3_bucket_lifecycle_configuration" "bronze" {
  bucket = aws_s3_bucket.bronze.id

  rule {
    id     = "transition-to-glacier"
    status = var.enable_lifecycle_rules ? "Enabled" : "Disabled"

    filter {}

    # After 90 days, move to Glacier for cost optimization
    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    # Delete old versions after 180 days
    noncurrent_version_expiration {
      noncurrent_days = 180
    }
  }
}

# -----------------------------------------------------------------------------
# Silver Layer - Cleaned and Validated Data
# -----------------------------------------------------------------------------
# Stores cleaned, validated, and conformed data
# Retention: Medium-term (reprocessing from bronze if needed)
# Access: Write by transformation jobs, read by analytics/ML

resource "aws_s3_bucket" "silver" {
  bucket = "${var.project_name}-${var.environment}-silver"

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-${var.environment}-silver"
      Layer       = "silver"
      Description = "Cleaned and validated data storage"
    }
  )
}

resource "aws_s3_bucket_versioning" "silver" {
  bucket = aws_s3_bucket.silver.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "silver" {
  bucket = aws_s3_bucket.silver.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "silver" {
  bucket = aws_s3_bucket.silver.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "silver" {
  bucket = aws_s3_bucket.silver.id

  rule {
    id     = "transition-to-ia"
    status = var.enable_lifecycle_rules ? "Enabled" : "Disabled"

    filter {}

    # After 60 days, move to Infrequent Access
    transition {
      days          = 60
      storage_class = "STANDARD_IA"
    }

    noncurrent_version_expiration {
      noncurrent_days = 90
    }
  }
}

# -----------------------------------------------------------------------------
# Gold Layer - Business-Ready Analytics Data
# -----------------------------------------------------------------------------
# Stores aggregated, business-ready data for analytics and reporting
# Retention: Active (frequently accessed)
# Access: Write by aggregation jobs, read by BI tools and analysts

resource "aws_s3_bucket" "gold" {
  bucket = "${var.project_name}-${var.environment}-gold"

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-${var.environment}-gold"
      Layer       = "gold"
      Description = "Business-ready analytics data storage"
    }
  )
}

resource "aws_s3_bucket_versioning" "gold" {
  bucket = aws_s3_bucket.gold.id

  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "gold" {
  bucket = aws_s3_bucket.gold.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "gold" {
  bucket = aws_s3_bucket.gold.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Gold layer kept in standard storage - frequently accessed for analytics
# No lifecycle transitions for gold layer as it's actively used

# -----------------------------------------------------------------------------
# Airflow DAGs Bucket
# -----------------------------------------------------------------------------
# Separate bucket for Airflow DAGs, plugins, and requirements.txt
# This bucket is read by AWS MWAA to sync DAGs

resource "aws_s3_bucket" "airflow" {
  bucket = "${var.project_name}-${var.environment}-airflow"

  tags = merge(
    var.tags,
    {
      Name        = "${var.project_name}-${var.environment}-airflow"
      Layer       = "airflow"
      Description = "Airflow DAGs, plugins, and requirements storage"
    }
  )
}

resource "aws_s3_bucket_versioning" "airflow" {
  bucket = aws_s3_bucket.airflow.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "airflow" {
  bucket = aws_s3_bucket.airflow.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "airflow" {
  bucket = aws_s3_bucket.airflow.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
