# BEES Data Engineering - Brewery Data Pipeline

> 🇺🇸 **[English Version](./README.md)** | 🇧🇷 Versão em Português

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

## 🎯 Sobre o Projeto

Pipeline de dados end-to-end implementando **Medallion Architecture** (Bronze → Silver → Gold) para ingestão, transformação, validação e análise de dados de cervejarias da **Open Brewery DB API**.

### ✨ Destaques do Projeto

- 🏗️ **Medallion Architecture** - Camadas Bronze/Silver/Gold com separação clara de responsabilidades
- 🔄 **Apache Airflow** - Orquestração completa com 8 tasks e gerenciamento de dependências
- ⚡ **PySpark** - Processamento distribuído de dados em escala
- 📊 **dbt** - 2 modelos SQL (staging + marts) com testes automatizados e documentação
- ✅ **Great Expectations** - 16 expectativas para validação de qualidade em todas as camadas
- 🐳 **Docker** - Ambiente completamente containerizado e reproduzível
- 🧪 **Testes abrangentes** - Cobertura focada em pipeline/orquestração (unit, integration, functional)
- 🚀 **CI/CD** - Pipelines automatizados com lint, test, security e docker build
- 📈 **Monitoring** - Dashboards Grafana, métricas Prometheus, alertas configurados
- ☁️ **Infrastructure as Code** - Terraform completo para deploy AWS (MWAA, RDS, S3)
- 🛠️ **Makefile** - 28+ comandos de automação para desenvolvimento e deployment

---

## 📊 Arquitetura

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

### Pré-requisitos

- **Docker** (24.0+) & **Docker Compose** (2.20+)
- **Git**
- **Make** (opcional, mas recomendado para automação)
- 8 GB RAM mínimo (16 GB recomendado)

> **💡 Compatibilidade de Plataforma:**
> Este projeto funciona nativamente em **Linux** e **macOS**. Usuários Windows precisarão de configurações adicionais (WSL2 recomendado) devido às dependências do Makefile e scripts bash. Alternativamente, use comandos Docker Compose diretamente ao invés do Make.

### Comandos Make Disponíveis

Este projeto usa **Makefile** para simplificar operações comuns:

**Setup & Docker:**
```bash
make init         # Inicializar projeto (cria .env do template)
make build        # Build das imagens Docker
make up           # Iniciar todos os serviços
make down         # Parar todos os serviços
make restart      # Reiniciar serviços
make logs         # Ver logs de todos os serviços
```

**Executar Pipeline:**
```bash
make airflow-ui   # Abrir Airflow UI no navegador
make seed-data    # Carregar dados de exemplo (100 primeiras cervejarias)
```

**Testes & Qualidade:**
```bash
make test              # Executar todos os testes com cobertura
make test-unit         # Apenas testes unitários
make test-integration  # Apenas testes de integração
make lint              # Executar linters (flake8, mypy)
make format            # Formatar código (black, isort)
```

**Database:**
```bash
make postgres-cli     # Conectar ao PostgreSQL CLI
make postgres-reset   # Resetar banco de dados
```

**dbt:**
```bash
make dbt-run      # Executar modelos dbt
make dbt-test     # Executar testes dbt
make dbt-docs     # Gerar e servir documentação dbt
```

**Terraform (AWS):**
```bash
make tf-plan-dev      # Planejar ambiente dev
make tf-apply-dev     # Aplicar ambiente dev
make tf-apply-prod    # Aplicar ambiente prod
```

**Utilitários:**
```bash
make shell            # Shell bash no container Airflow
make clean            # Limpar dados e volumes Docker
```

### 1. Clone e Inicie

```bash
# Clone o repositório
git clone https://github.com/YOUR_USERNAME/data_engineer_bees.git
cd data_engineer_bees

# Inicializar projeto (cria .env)
make init

# Inicie todos os containers
make up
# Ou alternativamente: docker-compose up -d

# Aguarde inicialização (~2 minutos)
make logs-airflow
# Ou alternativamente: docker-compose logs -f airflow-webserver
```

### 2. Acesse as Interfaces

| Serviço | URL | Credenciais |
|---------|-----|-------------|
| **Airflow** | http://localhost:8080 | admin / admin |
| **Grafana** | http://localhost:3000 | admin / admin |
| **Prometheus** | http://localhost:9090 | - |
| **PostgreSQL** | localhost:5432 | airflow / airflow |

### 3. Execute o Pipeline

```bash
# Via Airflow UI (abre automaticamente no navegador)
make airflow-ui
1. Ative a DAG 'brewery_data_pipeline'
2. Clique em "Trigger DAG"

# Ou acesse diretamente: http://localhost:8080

# Via CLI
make shell
airflow dags trigger brewery_data_pipeline

# Carregar dados de exemplo (primeiras 100 cervejarias)
make seed-data
```

### 4. Visualize os Resultados

```bash
# Ver dados no PostgreSQL
make postgres-cli

# Consultar tabela gold (agregação por tipo e localização)
SELECT * FROM gold.fat_breweries_by_type_location LIMIT 10;

# Consultar camadas silver e bronze
SELECT * FROM breweries_silver.tb_breweries LIMIT 5;
SELECT * FROM breweries_bronze.tb_breweries LIMIT 5;

# Ver arquivos Parquet
ls -lh data/bronze/breweries/
ls -lh data/silver/breweries/
ls -lh data/gold/breweries_by_type_location/
```

---

## 📁 Estrutura do Projeto

```
data_engineer_bees/
├── .github/
│   └── workflows/              # CI/CD Pipelines
│       ├── ci.yml              # Lint, test, security
│       ├── docker-build.yml    # Docker multi-stage build
│       └── release.yml         # Automated releases
│
├── airflow/
│   └── dags/
│       └── brewery_pipeline.py # Main DAG (8 tasks)
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
└── README.md                   # Este arquivo
```

---

## 🧪 Testes

### Filosofia de Testes

**Foco:** Pipeline/Orquestração

O projeto possui **testes abrangentes** organizados em 3 categorias:

| Categoria | Descrição |
|-----------|-----------|
| **Unit Tests** | Bronze layer patterns, Great Expectations framework integration |
| **Integration Tests** | Medallion flow end-to-end, pipeline orchestration, DAG structure |
| **Functional Tests** | Idempotency guarantees, re-execução segura, cleanup validation |

**Adicionalmente:**
- **16 Great Expectations** configuradas (bronze: 4, silver: 6, gold: 6)
- **1 dbt test customizado** (assert_positive_counts.sql)
- **8 Airflow tasks** com retry logic e error handling

### Executar Testes

```bash
# Usando Make (recomendado)
make test              # Executar todos os testes com cobertura
make test-unit         # Apenas testes unitários
make test-integration  # Apenas testes de integração

# Ou manualmente no container
make shell
pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# Por categoria
pytest tests/unit/ -v            # Testes unitários
pytest tests/integration/ -v     # Testes de integração
pytest tests/functional/ -v      # Testes funcionais

# CI local (lint + test + security)
./scripts/run_ci_checks.sh
```

### Métricas de Testes

- ✅ **5 arquivos de teste** cobrindo unit, integration e functional
- ⚡ **Execução rápida** com pytest
- 📊 **Cobertura focada** em pipeline e orquestração
- 🔄 **CI automatizado** em cada push/PR (GitHub Actions)
- ✨ **16 expectativas** Great Expectations em 3 checkpoints
- 🎯 **8 tasks Airflow** com retry e error handling

---

## 🔒 Segurança & Qualidade

### Code Quality

- **Black** - Formatação automática de código
- **isort** - Organização de imports
- **flake8** - Linting e style guide enforcement
- **pylint** - Análise estática avançada

### Security Scanning

- **Safety** - Vulnerability scanning em dependências Python
- **Bandit** - Security issues em código Python
- **Trivy** - Vulnerabilities em imagens Docker
- **Dependabot** - Automated dependency updates

### Data Quality

- **Great Expectations** - 16 expectativas configuradas
- **dbt tests** - Testes em modelos SQL
- **Custom validations** - Validações de negócio

---

## 📊 Métricas do Pipeline

### Dados Processados

- **9,038 breweries** processadas (dados completos da API)
- **14 tipos** de cervejarias (micro, nano, regional, brewpub, etc.)
- **3 camadas** (Bronze/Silver/Gold) seguindo Medallion Architecture
- **2 modelos dbt** (1 staging + 1 mart) com transformações SQL

### Performance

- **Bronze ingestion:** ~5-10s (API + persist)
- **Silver processing:** ~15-20s (PySpark transformations)
- **Gold aggregation:** ~10-15s (dbt models)
- **Total pipeline:** ~30-45s end-to-end

### Qualidade

- **16 Great Expectations** configuradas
- **0 expectativas falhando** em ambiente prod
- **100% coverage** em camadas críticas
- **Alertas automáticos** em falhas

---

## ☁️ Cloud Deployment (AWS)

### Terraform Infrastructure

O projeto inclui **Infrastructure as Code** completa para deploy na AWS:

```bash
# Deploy ambiente dev (~$150/mês)
cd terraform/environments/dev
terraform init
terraform plan
terraform apply

# Deploy ambiente prod (~$600/mês)
cd terraform/environments/prod
terraform init
terraform apply
```

### Recursos AWS Criados

| Serviço | Dev | Prod | Propósito |
|---------|-----|------|-----------|
| **MWAA** | mw1.small (1 worker) | mw1.medium (2-5 workers) | Managed Airflow |
| **RDS** | db.t3.micro, 20GB | db.t3.medium, 100GB, Multi-AZ | PostgreSQL |
| **S3** | 3 buckets | 3 buckets + lifecycle | Data lake |
| **VPC** | Single-AZ | Multi-AZ + NAT | Network isolation |
| **IAM** | Basic roles | Enhanced monitoring | Security |

**Documentação completa:** [`terraform/README.md`](terraform/README.md)

---

## 📈 Monitoring & Observability

### Dashboards Grafana

1. **Pipeline Overview** - Status geral, success rate, SLA
2. **Data Quality** - GE expectations, dbt test results
3. **Performance Metrics** - Task duration, throughput, latency

### Prometheus Metrics

- `airflow_dag_run_duration_seconds` - Duração de execuções
- `airflow_task_success_total` - Taxa de sucesso de tasks
- `airflow_task_failure_total` - Taxa de falha de tasks
- `great_expectations_validation_success` - Validações GE
- `data_lake_size_bytes` - Tamanho das camadas

### Alerting

Alertas configurados para:
- Pipeline failure (>2 falhas consecutivas)
- SLA breach (>60min de execução)
- Data quality issues (expectativas falhando)
- Low throughput (<100 records/min)

**Documentação completa:** [`docs/MONITORING.md`](docs/MONITORING.md)

---

## 🛠️ Stack Tecnológico

| Categoria | Tecnologia | Versão | Uso |
|-----------|------------|--------|-----|
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

## 📝 Documentação

### Documentos Principais

- **[MONITORING.md](docs/MONITORING.md)** - Guia completo de monitoramento e observabilidade (696 linhas)
- **[terraform/README.md](terraform/README.md)** - Infrastructure as Code para AWS deployment
- **[tests/README.md](tests/README.md)** - Filosofia e estratégia de testes
- **[Makefile](Makefile)** - 28+ comandos de automação para desenvolvimento

---

## 🎓 Decisões de Design

### Por que Medallion Architecture?

- **Separação clara** entre raw, cleaned e analytics
- **Rastreabilidade** - sempre possível voltar aos dados brutos
- **Flexibilidade** - diferentes consumidores em diferentes camadas
- **Escalabilidade** - processamento incremental por camada

### Por que PySpark na Silver?

- **Escalabilidade** - processa grandes volumes distribuídos
- **Performance** - transformações paralelizadas
- **Familiaridade** - sintaxe similar ao Pandas
- **Preparação** - silver deve ser otimizada para queries

### Por que dbt na Gold?

- **SQL nativo** - analistas podem contribuir
- **Testes embutidos** - validações declarativas
- **Documentação automática** - lineage e catalog
- **Incremental models** - eficiência em produção

### Por que Great Expectations?

- **Validação declarativa** - expectations legíveis
- **Profiling automático** - geração de suites
- **Data docs** - documentação visual de qualidade
- **Integração** - funciona bem com Airflow

---

### Padrões de Commit

- `feat:` Nova funcionalidade
- `fix:` Correção de bug
- `docs:` Documentação
- `test:` Testes
- `refactor:` Refatoração
- `chore:` Tarefas gerais

## 📞 Contato

**Everton Santos**
- LinkedIn: [Everton Santos](https://www.linkedin.com/in/santos-evertonds/)
- Email: evertonds@live.com

---