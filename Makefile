.PHONY: help init build up down restart logs test test-unit test-integration lint format airflow-ui postgres-cli seed-data clean tf-init tf-plan-dev tf-apply-dev tf-plan-prod tf-apply-prod tf-destroy tf-fmt tf-validate

# Default target
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

##@ General

help: ## Display this help message
	@echo "$(BLUE)BEES Brewery Pipeline - Make Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(YELLOW)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup & Initialization

init: ## Initialize project (create .env file from template)
	@echo "$(GREEN)Initializing project...$(NC)"
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "$(YELLOW)Created .env file from .env.example$(NC)"; \
		echo "$(YELLOW)Please edit .env and update the passwords and keys!$(NC)"; \
	else \
		echo "$(YELLOW).env file already exists, skipping...$(NC)"; \
	fi
	@mkdir -p data/bronze/breweries data/silver/breweries data/gold/breweries_by_type_location logs
	@echo "$(GREEN)Project initialized successfully!$(NC)"

##@ Docker Operations

build: ## Build Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	docker-compose build

up: ## Start all services
	@echo "$(GREEN)Starting all services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "$(YELLOW)Airflow UI: http://localhost:8080 (admin/admin)$(NC)"
	@echo "$(YELLOW)PostgreSQL: localhost:5432$(NC)"

down: ## Stop all services
	@echo "$(GREEN)Stopping all services...$(NC)"
	docker-compose down

restart: ## Restart all services
	@echo "$(GREEN)Restarting all services...$(NC)"
	docker-compose restart

logs: ## View logs from all services
	docker-compose logs -f

logs-airflow: ## View Airflow scheduler logs
	docker-compose logs -f airflow-scheduler

logs-postgres: ## View PostgreSQL logs
	docker-compose logs -f postgres

##@ Testing

test: ## Run all tests
	@echo "$(GREEN)Running all tests...$(NC)"
	docker-compose exec airflow-webserver pytest /opt/airflow/tests -v --cov=/opt/airflow/src --cov-report=html --cov-report=term

test-unit: ## Run unit tests only
	@echo "$(GREEN)Running unit tests...$(NC)"
	docker-compose exec airflow-webserver pytest /opt/airflow/tests/unit -v

test-integration: ## Run integration tests
	@echo "$(GREEN)Running integration tests...$(NC)"
	docker-compose exec airflow-webserver pytest /opt/airflow/tests/integration -v

##@ Code Quality

lint: ## Run linters (flake8, mypy)
	@echo "$(GREEN)Running linters...$(NC)"
	docker-compose exec airflow-webserver flake8 /opt/airflow/src /opt/airflow/dags --max-line-length=120
	docker-compose exec airflow-webserver mypy /opt/airflow/src --ignore-missing-imports

format: ## Format code with black and isort
	@echo "$(GREEN)Formatting code...$(NC)"
	docker-compose exec airflow-webserver black /opt/airflow/src /opt/airflow/dags /opt/airflow/tests
	docker-compose exec airflow-webserver isort /opt/airflow/src /opt/airflow/dags /opt/airflow/tests

check-format: ## Check if code is formatted correctly
	@echo "$(GREEN)Checking code format...$(NC)"
	docker-compose exec airflow-webserver black --check /opt/airflow/src /opt/airflow/dags /opt/airflow/tests
	docker-compose exec airflow-webserver isort --check-only /opt/airflow/src /opt/airflow/dags /opt/airflow/tests

##@ Database Operations

postgres-cli: ## Connect to PostgreSQL CLI
	@echo "$(GREEN)Connecting to PostgreSQL...$(NC)"
	docker-compose exec postgres psql -U airflow -d breweries

postgres-reset: ## Reset PostgreSQL database
	@echo "$(YELLOW)Resetting database... This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose exec postgres psql -U airflow -d breweries -c "DROP SCHEMA IF EXISTS bronze CASCADE; DROP SCHEMA IF EXISTS silver CASCADE; DROP SCHEMA IF EXISTS gold CASCADE;"; \
		docker-compose exec postgres psql -U airflow -d breweries -f /docker-entrypoint-initdb.d/init_db.sql; \
		echo "$(GREEN)Database reset successfully!$(NC)"; \
	fi

##@ Utilities

airflow-ui: ## Open Airflow UI in browser
	@echo "$(GREEN)Opening Airflow UI...$(NC)"
	@open http://localhost:8080 || xdg-open http://localhost:8080 || echo "Please open http://localhost:8080 in your browser"

seed-data: ## Load sample data for testing (first 100 breweries)
	@echo "$(GREEN)Loading sample data...$(NC)"
	docker-compose exec airflow-webserver python -c "from src.api.brewery_client import BreweryAPIClient; client = BreweryAPIClient(); data = client.fetch_all_breweries(max_pages=2); print(f'Fetched {len(data)} breweries')"

clean: ## Clean data directories and Docker volumes
	@echo "$(YELLOW)This will delete all data and Docker volumes!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		rm -rf data/bronze/* data/silver/* data/gold/* logs/*; \
		docker-compose down -v; \
		echo "$(GREEN)Cleaned successfully!$(NC)"; \
	fi

##@ Terraform (AWS Deployment)

tf-init: ## Initialize Terraform
	@echo "$(GREEN)Initializing Terraform...$(NC)"
	cd terraform && terraform init

tf-plan-dev: ## Plan dev environment
	@echo "$(GREEN)Planning dev environment...$(NC)"
	cd terraform && terraform workspace select dev || terraform workspace new dev
	cd terraform && terraform plan -var-file=environments/dev/terraform.tfvars

tf-apply-dev: ## Apply dev environment
	@echo "$(GREEN)Applying dev environment...$(NC)"
	cd terraform && terraform workspace select dev || terraform workspace new dev
	cd terraform && terraform apply -var-file=environments/dev/terraform.tfvars

tf-plan-prod: ## Plan prod environment
	@echo "$(GREEN)Planning prod environment...$(NC)"
	cd terraform && terraform workspace select prod || terraform workspace new prod
	cd terraform && terraform plan -var-file=environments/prod/terraform.tfvars

tf-apply-prod: ## Apply prod environment
	@echo "$(YELLOW)WARNING: This will deploy to production!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		cd terraform && terraform workspace select prod || terraform workspace new prod; \
		cd terraform && terraform apply -var-file=environments/prod/terraform.tfvars; \
	fi

tf-destroy: ## Destroy infrastructure (with confirmation)
	@echo "$(YELLOW)WARNING: This will destroy all infrastructure!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		cd terraform && terraform destroy; \
	fi

tf-fmt: ## Format Terraform files
	@echo "$(GREEN)Formatting Terraform files...$(NC)"
	cd terraform && terraform fmt -recursive

tf-validate: ## Validate Terraform configuration
	@echo "$(GREEN)Validating Terraform...$(NC)"
	cd terraform && terraform validate

##@ Development

shell: ## Open bash shell in Airflow container
	docker-compose exec airflow-webserver bash

python-shell: ## Open Python shell with project context
	docker-compose exec airflow-webserver python

dbt-run: ## Run dbt models
	@echo "$(GREEN)Running dbt models...$(NC)"
	docker-compose exec airflow-webserver dbt run --project-dir /opt/airflow/dbt_project

dbt-test: ## Run dbt tests
	@echo "$(GREEN)Running dbt tests...$(NC)"
	docker-compose exec airflow-webserver dbt test --project-dir /opt/airflow/dbt_project

dbt-docs: ## Generate and serve dbt documentation
	@echo "$(GREEN)Generating dbt documentation...$(NC)"
	docker-compose exec airflow-webserver dbt docs generate --project-dir /opt/airflow/dbt_project
	docker-compose exec airflow-webserver dbt docs serve --project-dir /opt/airflow/dbt_project
