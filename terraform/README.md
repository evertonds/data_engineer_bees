# BEES Breweries - Terraform Infrastructure

Infrastructure as Code (IaC) for the BEES Data Engineering platform using Terraform and AWS.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Directory Structure](#directory-structure)
- [Module Descriptions](#module-descriptions)
- [Usage Guide](#usage-guide)
- [Cost Estimates](#cost-estimates)
- [Security Considerations](#security-considerations)
- [Known Limitations](#known-limitations)
- [Future Enhancements](#future-enhancements)

## Overview

This Terraform configuration deploys a complete data engineering platform on AWS, demonstrating cloud infrastructure best practices for the BEES Data Engineering case study.

**Key Features:**
- Multi-environment support (dev, prod)
- Modular architecture for reusability
- Medallion architecture data lake (bronze, silver, gold)
- Managed Apache Airflow (AWS MWAA)
- PostgreSQL database (Amazon RDS)
- High availability options (Multi-AZ, auto-scaling)
- Security best practices (encryption, private subnets, IAM)

**Local → Cloud Mapping:**

| Local Component | AWS Service | Purpose |
|----------------|-------------|---------|
| Docker Airflow | AWS MWAA | Managed workflow orchestration |
| PostgreSQL | RDS PostgreSQL | Airflow metadata + data warehouse |
| Local storage (data/) | S3 Buckets | Medallion architecture data lake |
| Docker logs | CloudWatch Logs | Centralized logging |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         AWS Cloud                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                    VPC (10.x.0.0/16)                │   │
│  │                                                     │   │
│  │  ┌──────────────────┐      ┌──────────────────┐   │   │
│  │  │  Public Subnets  │      │ Private Subnets  │   │   │
│  │  │                  │      │                  │   │   │
│  │  │  - NAT Gateway   │──────│  - MWAA Workers  │   │   │
│  │  │  - Internet GW   │      │  - RDS (Multi-AZ)│   │   │
│  │  └──────────────────┘      └──────────────────┘   │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 S3 Data Lake                        │   │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐         │   │
│  │  │  Bronze  │→ │  Silver  │→ │   Gold   │         │   │
│  │  │   Raw    │  │ Cleaned  │  │ Analytics│         │   │
│  │  └──────────┘  └──────────┘  └──────────┘         │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              AWS MWAA (Airflow)                     │   │
│  │  - Webserver (Public/Private access)                │   │
│  │  - Scheduler (2-5 instances)                        │   │
│  │  - Workers (1-5 auto-scaling)                       │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │          RDS PostgreSQL (Multi-AZ)                  │   │
│  │  - Airflow metadata database                        │   │
│  │  - Data warehouse                                   │   │
│  │  - Automated backups (1-7 days)                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Required Tools

1. **Terraform** (>= 1.0)
   ```bash
   # Install via Homebrew (macOS)
   brew install terraform

   # Verify installation
   terraform version
   ```

2. **AWS CLI** (>= 2.0)
   ```bash
   # Install via Homebrew (macOS)
   brew install awscli

   # Verify installation
   aws --version
   ```

3. **AWS Account** with appropriate permissions
   - IAM permissions to create VPC, EC2, RDS, MWAA, S3, IAM roles
   - Recommended: AdministratorAccess for initial setup
   - Production: Use least-privilege custom IAM policy

### AWS Credentials Setup

Configure AWS credentials using one of these methods:

**Option 1: AWS CLI Configuration**
```bash
aws configure
# Enter: AWS Access Key ID, Secret Access Key, Region, Output format
```

**Option 2: Environment Variables**
```bash
export AWS_ACCESS_KEY_ID="your-access-key"
export AWS_SECRET_ACCESS_KEY="your-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

**Option 3: AWS Profiles**
```bash
# In ~/.aws/credentials
[bees-dev]
aws_access_key_id = your-dev-key
aws_secret_access_key = your-dev-secret

[bees-prod]
aws_access_key_id = your-prod-key
aws_secret_access_key = your-prod-secret

# Use profile
export AWS_PROFILE=bees-dev
```

### Service Quotas

Verify AWS service quotas for your account:
- **VPC**: Minimum 1 VPC available
- **Elastic IPs**: Minimum 2 (for NAT gateways)
- **RDS**: db.t3.micro and db.t3.medium instance types available
- **MWAA**: Service enabled in your region

## Directory Structure

```
terraform/
├── README.md                     # This file
├── backend.tf.example            # S3 backend configuration template
├── environments/                 # Environment-specific configurations
│   ├── dev/                      # Development environment
│   │   ├── main.tf               # Dev resource instantiation
│   │   ├── variables.tf          # Dev variables
│   │   ├── terraform.tfvars.example  # Example values (copy to terraform.tfvars)
│   │   └── outputs.tf            # Dev outputs
│   └── prod/                     # Production environment
│       ├── main.tf               # Prod resource instantiation
│       ├── variables.tf          # Prod variables
│       ├── terraform.tfvars.example  # Example values
│       └── outputs.tf            # Prod outputs
└── modules/                      # Reusable Terraform modules
    ├── storage/                  # S3 buckets (bronze, silver, gold)
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── database/                 # RDS PostgreSQL
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── airflow/                  # AWS MWAA environment
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    ├── networking/               # VPC, subnets, security groups
    │   ├── main.tf
    │   ├── variables.tf
    │   └── outputs.tf
    └── iam/                      # IAM roles and policies
        ├── main.tf
        ├── variables.tf
        └── outputs.tf
```

## Module Descriptions

### 1. Storage Module (`modules/storage/`)

**Purpose:** Create S3 buckets for medallion architecture data lake

**Resources:**
- 3 S3 buckets (bronze, silver, gold)
- Bucket versioning (data lineage)
- Server-side encryption (AES256)
- Lifecycle policies (storage tier optimization)
- Public access blocks (security)

**Configuration:**
- **Bronze**: Raw data from sources, lifecycle to Glacier after 90 days
- **Silver**: Cleaned/validated data, lifecycle to IA after 60 days
- **Gold**: Analytics-ready data, kept in Standard storage class

### 2. Database Module (`modules/database/`)

**Purpose:** Provision RDS PostgreSQL for Airflow metadata and data warehouse

**Resources:**
- RDS PostgreSQL instance (version 15.4)
- DB subnet group (Multi-AZ support)
- Parameter group (performance tuning)
- Security group (network access control)

**Configuration:**
- **Dev**: db.t3.micro, single-AZ, 20 GB, 1-day backups
- **Prod**: db.t3.medium, Multi-AZ, 100 GB, 7-day backups

### 3. Airflow Module (`modules/airflow/`)

**Purpose:** Deploy AWS MWAA (Managed Workflows for Apache Airflow)

**Resources:**
- MWAA environment (Airflow 2.7.2)
- S3 bucket for DAGs and plugins
- CloudWatch log groups (5 types)
- Execution IAM role

**Configuration:**
- **Dev**: mw1.small, 1 worker, 3-day log retention
- **Prod**: mw1.medium, 2-5 workers (auto-scaling), 30-day log retention

### 4. Networking Module (`modules/networking/`)

**Purpose:** Create VPC and network infrastructure

**Resources:**
- VPC (custom CIDR)
- 2 public subnets (different AZs)
- 2 private subnets (different AZs)
- Internet gateway
- NAT gateway (prod only, cost optimization)
- Route tables
- Security groups (MWAA, RDS)

**Configuration:**
- **Dev**: No NAT gateway (cost savings, limited internet access)
- **Prod**: NAT gateway enabled (internet access for private subnets)

### 5. IAM Module (`modules/iam/`)

**Purpose:** Create IAM roles and policies for service access

**Resources:**
- MWAA execution role
- S3 access policies (data lake + DAGs)
- CloudWatch Logs policies
- RDS access policies (optional)
- Secrets Manager policies (prod)
- RDS monitoring role (prod)

**Configuration:**
- Least-privilege access patterns
- Service-specific policies
- Separate roles for different services

## Usage Guide

### Initial Setup

1. **Clone the repository**
   ```bash
   cd /Users/everton.santos/Desktop/personal_projects/data_engineer_bees
   ```

2. **Choose environment (dev or prod)**
   ```bash
   cd terraform/environments/dev
   # OR
   cd terraform/environments/prod
   ```

3. **Copy example variables**
   ```bash
   cp terraform.tfvars.example terraform.tfvars
   ```

4. **Edit terraform.tfvars**
   ```bash
   # Set your values (especially db_password!)
   vim terraform.tfvars
   ```

   **IMPORTANT:** Never commit `terraform.tfvars` to Git!
   ```bash
   echo "terraform.tfvars" >> .gitignore
   ```

### Deploy Development Environment

```bash
# Navigate to dev environment
cd terraform/environments/dev

# Initialize Terraform (downloads providers)
terraform init

# Preview changes
terraform plan

# Apply changes (type 'yes' when prompted)
terraform apply

# View outputs
terraform output

# Get specific output
terraform output airflow_webserver_url
```

**Expected deployment time:** 20-30 minutes (MWAA takes ~20 minutes)

### Deploy Production Environment

```bash
# Navigate to prod environment
cd terraform/environments/prod

# Initialize Terraform
terraform init

# Preview changes (review carefully for prod!)
terraform plan

# Apply with auto-approve (use cautiously)
terraform apply -auto-approve

# View outputs
terraform output
```

**Expected deployment time:** 25-35 minutes

### Upload Airflow DAGs

After deployment, upload DAGs to S3:

```bash
# Get the S3 bucket name from outputs
terraform output airflow_bucket

# Sync DAGs to S3
aws s3 sync ../../airflow/dags s3://$(terraform output -raw airflow_bucket)/dags/ --delete

# Verify upload
aws s3 ls s3://$(terraform output -raw airflow_bucket)/dags/
```

### Access Airflow Web UI

```bash
# Get webserver URL
terraform output airflow_webserver_url

# Get login token (valid for 60 seconds)
aws mwaa create-web-login-token --name $(terraform output -raw airflow_environment_name)

# Open in browser and use the token
```

### Connect to Database

```bash
# Get connection details
terraform output database_endpoint

# Connect using psql
PGPASSWORD=your_password psql \
  -h $(terraform output -raw database_endpoint | cut -d: -f1) \
  -U airflow \
  -d airflow
```

### Destroy Resources

**⚠️ WARNING:** This will delete all resources and data!

```bash
# Development (safe to destroy)
cd terraform/environments/dev
terraform destroy

# Production (be extra careful!)
cd terraform/environments/prod
terraform destroy
```

## Cost Estimates

### Development Environment

**Monthly Cost:** ~$150-200

| Service | Configuration | Cost |
|---------|--------------|------|
| RDS PostgreSQL | db.t3.micro, 20 GB, Single-AZ | ~$15 |
| MWAA | mw1.small, 1 worker | ~$100-120 |
| S3 | 50 GB storage, versioning | ~$5 |
| CloudWatch Logs | 3-day retention | ~$3 |
| Data Transfer | Minimal | ~$5 |
| **Total** | | **~$150-200** |

**Cost Optimization:**
- No NAT gateway (~$35/month savings)
- Minimal instance sizes
- Shorter log retention
- Single-AZ deployment

### Production Environment

**Monthly Cost:** ~$500-700

| Service | Configuration | Cost |
|---------|--------------|------|
| RDS PostgreSQL | db.t3.medium, 100 GB, Multi-AZ | ~$100 |
| MWAA | mw1.medium, 2-5 workers | ~$350-450 |
| NAT Gateway | 1 gateway + data transfer | ~$35 |
| S3 | 200 GB storage, versioning, lifecycle | ~$20 |
| CloudWatch Logs | 30-day retention | ~$10 |
| Data Transfer | Moderate usage | ~$15 |
| **Total** | | **~$500-700** |

**Cost Considerations:**
- MWAA is the largest cost component (auto-scaling workers)
- NAT Gateway has both hourly ($0.045/hr) and data transfer costs
- Multi-AZ RDS doubles compute cost but provides HA
- Consider Reserved Instances for 30-50% savings on RDS

### Cost Monitoring

```bash
# View AWS Cost Explorer (requires AWS Console access)
# Or use AWS CLI
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics "UnblendedCost" \
  --group-by Type=SERVICE
```

## Security Considerations

### Data Protection

1. **Encryption at Rest**
   - S3: Server-side encryption (AES256)
   - RDS: Storage encryption enabled
   - MWAA: Environment encryption enabled

2. **Encryption in Transit**
   - RDS: SSL/TLS connections enforced
   - S3: HTTPS required for all operations
   - MWAA: TLS for webserver and workers

### Network Security

1. **Private Subnets**
   - RDS deployed in private subnets (no public access)
   - MWAA workers in private subnets
   - Internet access via NAT gateway (prod only)

2. **Security Groups**
   - RDS: Only accepts connections from MWAA security group
   - MWAA: Self-referencing rules for internal communication
   - Principle of least privilege

3. **Public Access Blocks**
   - All S3 buckets have public access blocked
   - RDS publicly_accessible = false

### Identity and Access Management

1. **IAM Roles**
   - MWAA execution role with minimal required permissions
   - Separate roles for different services
   - No hardcoded credentials in code

2. **Secrets Management**
   - **Dev**: Passwords in terraform.tfvars (NOT committed to Git)
   - **Prod**: AWS Secrets Manager (recommended, commented in code)
   - Rotate credentials regularly

### Compliance and Audit

1. **CloudWatch Logs**
   - All Airflow logs sent to CloudWatch
   - RDS logs enabled (connections, disconnections, duration)
   - Log retention configured per environment

2. **Backup and Recovery**
   - RDS automated backups (1-7 days retention)
   - S3 versioning enabled for data lineage
   - Final snapshot on RDS deletion (prod)

3. **Tagging Strategy**
   - All resources tagged with Project, Environment, ManagedBy
   - Cost allocation tags for billing analysis

## Known Limitations

### Simplifications (For Demonstration)

This is a **demonstration project** to show IaC knowledge, not a production-ready deployment. Simplifications include:

1. **No KMS Custom Keys**: Using S3-managed encryption (SSE-S3) instead of KMS for simplicity
2. **No Secrets Manager Integration**: Database passwords in variables (production MUST use Secrets Manager)
3. **No VPC Endpoints**: Direct internet access via NAT gateway (S3/CloudWatch endpoints would reduce costs)
4. **No Custom Domains**: Using default MWAA webserver URL (no Route53 configuration)
5. **Simplified Security Groups**: Basic rules only (production needs more granular controls)
6. **No CI/CD Pipeline**: Manual terraform apply (production should use GitOps/Terraform Cloud)
7. **Single Region**: us-east-1 only (production might need multi-region)
8. **No Monitoring Alerts**: No CloudWatch alarms configured (production needs alerting)
9. **Basic Networking**: Single VPC, no VPC peering or Transit Gateway
10. **No DR/Backup Strategy**: Beyond RDS automated backups

### Validation Status

✅ **Can be validated:**
- Terraform syntax (`terraform fmt -check`)
- Terraform validity (`terraform validate`)
- Module structure and organization
- Variable definitions and types

❌ **Cannot be validated without AWS deployment:**
- Actual resource creation
- Integration between services
- Performance and costs
- Security group rules effectiveness

## Future Enhancements

### Phase 1: Production Hardening

- [ ] Integrate AWS Secrets Manager for credential management
- [ ] Add KMS custom keys for encryption control
- [ ] Implement VPC endpoints (S3, CloudWatch, Secrets Manager)
- [ ] Configure custom domain with Route53 and SSL certificate
- [ ] Add CloudWatch alarms for critical metrics
- [ ] Implement automated backup strategy

### Phase 2: Observability

- [ ] Add AWS CloudWatch dashboards
- [ ] Configure SNS topics for alerting
- [ ] Implement log aggregation and analysis
- [ ] Add AWS X-Ray for distributed tracing
- [ ] Configure Cost Anomaly Detection

### Phase 3: CI/CD Integration

- [ ] GitHub Actions workflow for Terraform
- [ ] Automated terraform plan on pull requests
- [ ] Automated terraform apply on merge to main
- [ ] State file encryption and remote backend
- [ ] Terraform Cloud integration

### Phase 4: Advanced Features

- [ ] Multi-region deployment
- [ ] Disaster recovery strategy
- [ ] Read replicas for RDS
- [ ] AWS Glue Data Catalog integration
- [ ] Lake Formation for data governance
- [ ] Step Functions for complex orchestration
- [ ] Lambda functions for serverless processing

### Phase 5: Optimization

- [ ] Reserved Instances for cost savings
- [ ] Spot Instances for non-critical workloads
- [ ] S3 Intelligent-Tiering
- [ ] RDS Performance Insights analysis
- [ ] Auto Scaling policies tuning

## Troubleshooting

### Common Issues

**Issue: "Error: Error locking state"**
```bash
# Someone else is running terraform, wait for them to finish
# Or if process crashed, manually remove lock:
aws dynamodb delete-item \
  --table-name terraform-state-lock \
  --key '{"LockID":{"S":"<lock-id>"}}'
```

**Issue: "Error creating DB Instance: DBSubnetGroupNotFoundFault"**
```bash
# Networking module must be created first
# Ensure depends_on is specified in environment main.tf
```

**Issue: "Error creating MWAA Environment: ValidationException"**
```bash
# Check MWAA service availability in your region
aws mwaa list-environments --region us-east-1
# Check subnet configuration (must be in different AZs)
```

**Issue: High AWS costs**
```bash
# Destroy dev environment when not in use
cd terraform/environments/dev
terraform destroy

# Production: Consider auto-stop schedule for RDS (if non-critical)
```

## Additional Resources

- [Terraform Documentation](https://www.terraform.io/docs)
- [AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS MWAA Documentation](https://docs.aws.amazon.com/mwaa/)
- [Terraform Best Practices](https://www.terraform.io/docs/cloud/guides/recommended-practices/index.html)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

## Support

For issues related to:
- **Terraform code**: Check module documentation and AWS provider docs
- **AWS services**: Refer to AWS documentation and support
- **BEES case study**: Contact project maintainer

## License

This is a demonstration project for the BEES Data Engineering case study.

---

**Last Updated:** 2024-01-26
**Terraform Version:** >= 1.0
**AWS Provider Version:** ~> 5.0
**Author:** Everton Santos
