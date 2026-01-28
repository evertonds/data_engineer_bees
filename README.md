# BEES Data Engineering - Brewery Data Pipeline

> 🇺🇸 English Version | 🇧🇷 **[Versão em Português](./README.pt-BR.md)**

[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.8.0-017cee.svg)](https://airflow.apache.org/)
[![PySpark](https://img.shields.io/badge/PySpark-3.5.0-orange.svg)](https://spark.apache.org/)
[![dbt](https://img.shields.io/badge/dbt-1.7.0-ff6849.svg)](https://www.getdbt.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-24.0-2496ed.svg)](https://www.docker.com/)
[![Terraform](https://img.shields.io/badge/Terraform-1.14-623CE4.svg)](https://www.terraform.io/)
[![Great Expectations](https://img.shields.io/badge/Great%20Expectations-0.18-green.svg)](https://greatexpectations.io/)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/imports-isort-1674b1.svg)](https://pycqa.github.io/isort/)
[![Linting: flake8](https://img.shields.io/badge/linting-flake8-blue.svg)](https://flake8.pycqa.org/)

---

## 🎯 About the Project

End-to-end data pipeline implementing **Medallion Architecture** (Bronze → Silver → Gold) for ingestion, transformation, validation, and analysis of brewery data from the **Open Brewery DB API**.

### ✨ Project Highlights

- 🏗️ **Medallion Architecture** - Bronze/Silver/Gold layers with clear separation of concerns
- 🔄 **Apache Airflow** - Complete orchestration with 8 tasks and dependency management
- ⚡ **PySpark** - Distributed data processing at scale
- 📊 **dbt** - 2 SQL models (staging + marts) with automated tests and documentation
- ✅ **Great Expectations** - 16 expectations for quality validation across all layers
- 🐳 **Docker** - Fully containerized and reproducible environment
- 🧪 **Comprehensive Testing** - Pipeline/orchestration focused coverage (unit, integration, functional)
- 🚀 **CI/CD** - Automated pipelines with lint, test, security, and docker build
- 📈 **Monitoring** - Grafana dashboards, Prometheus metrics, configured alerts
- ☁️ **Infrastructure as Code** - Complete Terraform for AWS deployment (MWAA, RDS, S3)
- 🛠️ **Makefile** - 28+ automation commands for development and deployment

---

## 📊 Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                     AIRFLOW ORCHESTRATION                           │
│                   (8 tasks, DAG dependencies)                       │
└────────────────────────────────────────────────────────────────────┘
                                ↓
┌────────────────────────────────────────────────────────────────────┐
│  BRONZE LAYER - Raw Data Ingestion                                 │
│  ─────────────────────────────────────────────────────────────     │
│  • API Extraction (Open Brewery DB)                                │
│  • Schema-on-read (minimal transformations)                        │
│  • Dual persistence: Parquet (data/) + PostgreSQL                  │
│  • 9,038 breweries × 14 types                                      │
│                                                                     │
│  Validations:                                                       │
│  ✓ Row count (expect_table_row_count_to_be_between)               │
│  ✓ No nulls in ID (expect_column_values_to_not_be_null)           │
│  ✓ Valid brewery types (expect_column_values_to_be_in_set)        │
└────────────────────────────────────────────────────────────────────┘
                                ↓
┌────────────────────────────────────────────────────────────────────┐
│  SILVER LAYER - Cleaned & Enriched Data                            │
│  ────────────────────────────────────────────────────────────      │
│  • PySpark transformations (address cleaning, geocoding)           │
│  • Data quality enrichment                                         │
│  • Deduplication & standardization                                 │
│  • Type conversions and validation                                 │
│                                                                     │
│  Validations:                                                       │
│  ✓ Geocoding quality (expect_column_mean_to_be_between)           │
│  ✓ Valid coordinates (expect_column_values_to_be_between)         │
│  ✓ No duplicate IDs (expect_column_values_to_be_unique)           │
└────────────────────────────────────────────────────────────────────┘
                                ↓
┌────────────────────────────────────────────────────────────────────┐
│  GOLD LAYER - Business Aggregates & Analytics                      │
│  ────────────────────────────────────────────────────────────      │
│  • dbt transformations (2 models: staging + marts)                 │
│  • Fact table: fat_breweries_by_type_location                      │
│  • Business metrics and aggregations                               │
│  • Aggregated view: quantity of breweries per type and location    │
│                                                                     │
│  Validations:                                                       │
│  ✓ dbt tests (unique, not_null, relationships, custom)            │
│  ✓ Great Expectations on final aggregates                          │
│  ✓ Business rule validation                                        │
└────────────────────────────────────────────────────────────────────┘
                                ↓
┌────────────────────────────────────────────────────────────────────┐
│  MONITORING & OBSERVABILITY                                         │
│  ──────────────────────────────────────────────────────────────    │
│  • Grafana Dashboards (pipeline, data quality, performance)        │
│  • Prometheus Metrics (task duration, success rate, SLA)           │
│  • Alerting (email, Slack, PagerDuty)                             │
│  • CloudWatch integration (AWS deployment)                         │
└────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker** (24.0+) & **Docker Compose** (2.20+)
- **Git**
- **Make** (optional but recommended for automation)
- 8 GB RAM minimum (16 GB recommended)

### Available Make Commands

This project uses a **Makefile** to simplify common operations:

**Setup & Docker:**
```bash
make init         # Initialize project (creates .env from template)
make build        # Build Docker images
make up           # Start all services
make down         # Stop all services
make restart      # Restart services
make logs         # View logs from all services
```

**Run Pipeline:**
```bash
make airflow-ui   # Open Airflow UI in browser
make seed-data    # Load sample data (first 100 breweries)
```

**Tests & Quality:**
```bash
make test              # Run all tests with coverage
make test-unit         # Unit tests only
make test-integration  # Integration tests only
make lint              # Run linters (flake8, mypy)
make format            # Format code (black, isort)
```

**Database:**
```bash
make postgres-cli     # Connect to PostgreSQL CLI
make postgres-reset   # Reset database
```

**dbt:**
```bash
make dbt-run      # Run dbt models
make dbt-test     # Run dbt tests
make dbt-docs     # Generate and serve dbt documentation
```

**Terraform (AWS):**
```bash
make tf-plan-dev      # Plan dev environment
make tf-apply-dev     # Apply dev environment
make tf-apply-prod    # Apply prod environment
```

**Utilities:**
```bash
make shell            # Bash shell in Airflow container
make clean            # Clean data and Docker volumes
```

### 1. Clone and Start

```bash
# Clone repository
git clone https://github.com/YOUR_USERNAME/data_engineer_bees.git
cd data_engineer_bees

# Initialize project (creates .env)
make init

# Start all containers
make up
# Or alternatively: docker-compose up -d

# Wait for initialization (~2 minutes)
make logs-airflow
# Or alternatively: docker-compose logs -f airflow-webserver
```

### 2. Access Interfaces

| Service | URL | Credentials |
|---------|-----|-------------|
| **Airflow** | http://localhost:8080 | admin / admin |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **PostgreSQL** | localhost:5432 | airflow / airflow |

### 3. Run the Pipeline

```bash
# Via Airflow UI (opens automatically in browser)
make airflow-ui
1. Enable DAG 'brewery_data_pipeline'
2. Click "Trigger DAG"

# Or access directly: http://localhost:8080

# Via CLI
make shell
airflow dags trigger brewery_data_pipeline

# Load sample data (first 100 breweries)
make seed-data
```

### 4. View Results

```bash
# View data in PostgreSQL
make postgres-cli

# Query gold table (aggregation by type and location)
SELECT * FROM gold.fat_breweries_by_type_location LIMIT 10;

# Query silver and bronze layers
SELECT * FROM breweries_silver.tb_breweries LIMIT 5;
SELECT * FROM breweries_bronze.tb_breweries LIMIT 5;

# View Parquet files
ls -lh data/bronze/breweries/
ls -lh data/silver/breweries/
ls -lh data/gold/breweries_by_type_location/
```

---

## 📁 Project Structure

```
data_engineer_bees/
├── .github/
│   └── workflows/              # CI/CD Pipelines
│       ├── ci.yml              # Lint, test, security
│       ├── docker-build.yml    # Docker multi-stage build
│       └── release.yml         # Automated releases
│
├── dags/
│   └── brewery_pipeline.py     # Main DAG (8 tasks)
│
├── src/
│   ├── api/
│   │   └── brewery_client.py       # API client + retry logic
│   ├── processors/
│   │   ├── bronze_processor.py     # Raw ingestion
│   │   └── silver_processor.py     # PySpark transformations
│   ├── storage/
│   │   ├── base_storage.py         # Abstract storage interface
│   │   ├── local_storage.py        # Local file system storage
│   │   ├── s3_storage.py           # AWS S3 storage
│   │   ├── postgres_loader.py      # PostgreSQL loader
│   │   └── storage_factory.py      # Storage factory pattern
│   ├── validation/
│   │   └── ge_validator.py         # Great Expectations integration
│   └── config/
│       └── settings.py             # Configuration management
│
├── dbt_project/
│   ├── models/
│   │   ├── staging/            # Staging models
│   │   │   └── stg_breweries.sql
│   │   └── marts/              # Gold layer marts
│   │       └── fat_breweries_by_type_location.sql
│   ├── tests/                  # Custom dbt tests
│   │   └── assert_positive_counts.sql
│   ├── dbt_project.yml
│   ├── profiles.yml
│   └── packages.yml
│
├── great_expectations/
│   ├── expectations/
│   │   ├── bronze_suite.json   # Bronze validations
│   │   ├── silver_suite.json   # Silver validations
│   │   └── gold_suite.json     # Gold validations
│   └── checkpoints/
│       └── brewery_checkpoint.yml
│
├── monitoring/
│   ├── grafana/
│   │   └── dashboards/         # 3 dashboards
│   │       ├── pipeline_overview.json
│   │       ├── data_quality.json
│   │       └── performance_metrics.json
│   ├── prometheus/
│   │   └── prometheus.yml      # Metrics config
│   └── alerting/
│       └── alert_rules.yml     # Alert definitions
│
├── terraform/
│   ├── modules/                # 5 reusable modules
│   │   ├── storage/            # S3 buckets (bronze, silver, gold)
│   │   ├── database/           # RDS PostgreSQL
│   │   ├── airflow/            # AWS MWAA
│   │   ├── networking/         # VPC, subnets, SGs
│   │   └── iam/                # Roles and policies
│   └── environments/
│       ├── dev/                # Dev environment (~$150/mo)
│       └── prod/               # Prod environment (~$600/mo)
│
├── tests/
│   ├── unit/                   # Unit tests (bronze, GE framework)
│   ├── integration/            # Integration tests (medallion flow, DAG orchestration)
│   └── functional/             # Functional tests (idempotency)
│
├── scripts/
│   ├── run_ci_checks.sh        # Local CI validation
│   └── init_db.sql             # Database initialization
│
├── docs/
│   └── MONITORING.md           # Comprehensive monitoring guide (696 lines)
│
├── docker-compose.yml          # Multi-container orchestration
├── Dockerfile                  # Multi-stage build
├── requirements.txt            # Python dependencies
├── pyproject.toml              # Project configuration
├── Makefile                    # Automation commands
└── README.md                   # This file
```

---

## 🧪 Testing

### Testing Philosophy

**Focus:** Pipeline/Orchestration

The project has **comprehensive tests** organized in 3 categories:

| Category | Description |
|----------|-------------|
| **Unit Tests** | Bronze layer patterns, Great Expectations framework integration |
| **Integration Tests** | End-to-end medallion flow, pipeline orchestration, DAG structure |
| **Functional Tests** | Idempotency guarantees, safe re-execution, cleanup validation |

**Additionally:**
- **16 Great Expectations** configured (bronze: 4, silver: 6, gold: 6)
- **1 custom dbt test** (assert_positive_counts.sql)
- **8 Airflow tasks** with retry logic and error handling

### Run Tests

```bash
# Using Make (recommended)
make test              # Run all tests with coverage
make test-unit         # Unit tests only
make test-integration  # Integration tests only

# Or manually in container
make shell
pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# By category
pytest tests/unit/ -v            # Unit tests
pytest tests/integration/ -v     # Integration tests
pytest tests/functional/ -v      # Functional tests

# Local CI (lint + test + security)
./scripts/run_ci_checks.sh
```

### Test Metrics

- ✅ **5 test files** covering unit, integration, and functional
- ⚡ **Fast execution** with pytest
- 📊 **Focused coverage** on pipeline and orchestration
- 🔄 **Automated CI** on every push/PR (GitHub Actions)
- ✨ **16 expectations** in 3 Great Expectations checkpoints
- 🎯 **8 Airflow tasks** with retry and error handling

---

## 🔒 Security & Quality

### Code Quality

- **Black** - Automatic code formatting
- **isort** - Import organization
- **flake8** - Linting and style guide enforcement
- **pylint** - Advanced static analysis

### Security Scanning

- **Safety** - Vulnerability scanning in Python dependencies
- **Bandit** - Security issues in Python code
- **Trivy** - Vulnerabilities in Docker images
- **Dependabot** - Automated dependency updates

### Data Quality

- **Great Expectations** - 16 configured expectations
- **dbt tests** - Tests on SQL models
- **Custom validations** - Business rule validation

---

## 📊 Pipeline Metrics

### Data Processed

- **9,038 breweries** processed (complete API data)
- **14 types** of breweries (micro, nano, regional, brewpub, etc.)
- **3 layers** (Bronze/Silver/Gold) following Medallion Architecture
- **2 dbt models** (1 staging + 1 mart) with SQL transformations

### Performance

- **Bronze ingestion:** ~5-10s (API + persist)
- **Silver processing:** ~15-20s (PySpark transformations)
- **Gold aggregation:** ~10-15s (dbt models)
- **Total pipeline:** ~30-45s end-to-end

### Quality

- **16 Great Expectations** configured
- **0 failing expectations** in prod environment
- **100% coverage** on critical layers
- **Automatic alerts** on failures

---

## ☁️ Cloud Deployment (AWS)

### Terraform Infrastructure

The project includes complete **Infrastructure as Code** for AWS deployment:

```bash
# Deploy dev environment (~$150/month)
cd terraform/environments/dev
terraform init
terraform plan
terraform apply

# Deploy prod environment (~$600/month)
cd terraform/environments/prod
terraform init
terraform apply
```

### AWS Resources Created

| Service | Dev | Prod | Purpose |
|---------|-----|------|---------|
| **MWAA** | mw1.small (1 worker) | mw1.medium (2-5 workers) | Managed Airflow |
| **RDS** | db.t3.micro, 20GB | db.t3.medium, 100GB, Multi-AZ | PostgreSQL |
| **S3** | 3 buckets | 3 buckets + lifecycle | Data lake |
| **VPC** | Single-AZ | Multi-AZ + NAT | Network isolation |
| **IAM** | Basic roles | Enhanced monitoring | Security |

**Complete documentation:** [`terraform/README.md`](terraform/README.md)

---

## 📈 Monitoring & Observability

### Grafana Dashboards

1. **Pipeline Overview** - Overall status, success rate, SLA
2. **Data Quality** - GE expectations, dbt test results
3. **Performance Metrics** - Task duration, throughput, latency

### Prometheus Metrics

- `airflow_dag_run_duration_seconds` - Execution duration
- `airflow_task_success_total` - Task success rate
- `airflow_task_failure_total` - Task failure rate
- `great_expectations_validation_success` - GE validations
- `data_lake_size_bytes` - Layer sizes

### Alerting

Configured alerts for:
- Pipeline failure (>2 consecutive failures)
- SLA breach (>60min execution)
- Data quality issues (failing expectations)
- Low throughput (<100 records/min)

**Complete documentation:** [`docs/MONITORING.md`](docs/MONITORING.md)

---

## 🛠️ Technology Stack

| Category | Technology | Version | Use |
|----------|------------|---------|-----|
| **Orchestration** | Apache Airflow | 2.8.0 | Workflow management |
| **Processing** | PySpark | 3.5.0 | Distributed data processing |
| **Transformation** | dbt | 1.7.0 | SQL transformations + tests |
| **Database** | PostgreSQL | 15 | Airflow metadata + data warehouse |
| **Data Quality** | Great Expectations | 0.18 | Data validation |
| **Monitoring** | Grafana + Prometheus | 10.x + 2.x | Metrics & dashboards |
| **Infrastructure** | Terraform | 1.14 | IaC for AWS |
| **Containerization** | Docker | 24.0 | Environment isolation |
| **CI/CD** | GitHub Actions | - | Automated pipelines |
| **Testing** | pytest | 7.4 | Test framework |
| **Code Quality** | Black, isort, flake8 | - | Linting & formatting |
| **Security** | Safety, Bandit, Trivy | - | Vulnerability scanning |

---

## 📝 Documentation

### Main Documents

- **[MONITORING.md](docs/MONITORING.md)** - Complete monitoring and observability guide (696 lines)
- **[terraform/README.md](terraform/README.md)** - Infrastructure as Code for AWS deployment
- **[tests/README.md](tests/README.md)** - Testing philosophy and strategy
- **[Makefile](Makefile)** - 28+ automation commands for development

---

## 🎓 Design Decisions

### Why Medallion Architecture?

- **Clear separation** between raw, cleaned, and analytics
- **Traceability** - always possible to return to raw data
- **Flexibility** - different consumers at different layers
- **Scalability** - incremental processing per layer

### Why PySpark in Silver?

- **Scalability** - processes large distributed volumes
- **Performance** - parallelized transformations
- **Familiarity** - Pandas-like syntax
- **Preparation** - silver should be optimized for queries

### Why dbt in Gold?

- **Native SQL** - analysts can contribute
- **Built-in tests** - declarative validations
- **Automatic documentation** - lineage and catalog
- **Incremental models** - production efficiency

### Why Great Expectations?

- **Declarative validation** - readable expectations
- **Automatic profiling** - suite generation
- **Data docs** - visual quality documentation
- **Integration** - works well with Airflow

---

### Commit Patterns

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Refactoring
- `chore:` General tasks

## 📞 Contact

**Everton Santos**
- GitHub: [@YOUR_USERNAME](https://github.com/YOUR_USERNAME)
- LinkedIn: [Everton Santos](https://www.linkedin.com/in/santos-evertonds/)
- Email: evertonds@live.com

---
