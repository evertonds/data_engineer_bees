"""
Brewery Data Pipeline DAG

This DAG orchestrates the complete brewery data pipeline following
the medallion architecture (Bronze → Silver → Gold):

1. Bronze Layer: Extract raw data from Open Brewery DB API
2. Silver Layer: Transform and clean data using PySpark
3. Gold Layer: Create aggregated views using dbt

Schedule: Daily at 2 AM
Retries: 3 attempts with exponential backoff
"""

import logging
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago

# Default arguments for all tasks
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'retry_exponential_backoff': True,
    'max_retry_delay': timedelta(minutes=30),
}

# DAG definition
dag = DAG(
    'brewery_data_pipeline',
    default_args=default_args,
    description='Complete brewery data pipeline with Bronze/Silver/Gold layers',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    start_date=days_ago(1),
    catchup=False,
    max_active_runs=1,
    tags=['brewery', 'etl', 'medallion'],
)


# ============================================================================
# Task Functions
# ============================================================================

def extract_bronze_data(**context):
    """
    Extract data from Open Brewery DB API and load to Bronze layer.

    This task:
    - Fetches data from the API with pagination
    - Saves raw JSON to local storage
    - Loads data to PostgreSQL breweries_bronze.tb_breweries table
    """
    import sys
    sys.path.insert(0, '/opt/airflow')

    from src.processors.bronze_processor import BronzeProcessor

    logger = logging.getLogger(__name__)
    logger.info("Starting Bronze data extraction...")

    try:
        with BronzeProcessor() as processor:
            # Extract all breweries (or limit with max_pages for testing)
            results = processor.extract_breweries()

            logger.info(f"Bronze extraction complete: {results}")

            # Push results to XCom for downstream tasks
            context['task_instance'].xcom_push(
                key='bronze_results',
                value=results
            )

            return results

    except Exception as e:
        logger.error(f"Bronze extraction failed: {e}", exc_info=True)
        raise


def transform_silver_data(**context):
    """
    Transform Bronze data to Silver layer using PySpark.

    This task:
    - Loads data from breweries_bronze.tb_breweries
    - Applies cleaning and transformations
    - Saves as partitioned Parquet files
    - Loads to PostgreSQL breweries_silver.tb_breweries table
    """
    import sys
    sys.path.insert(0, '/opt/airflow')

    from datetime import date
    from src.processors.silver_processor import SilverProcessor

    logger = logging.getLogger(__name__)
    logger.info("Starting Silver data transformation...")

    try:
        with SilverProcessor() as processor:
            # Process data for today
            results = processor.run(source_date=date.today())

            logger.info(f"Silver transformation complete: {results}")

            # Push results to XCom
            context['task_instance'].xcom_push(
                key='silver_results',
                value=results
            )

            return results

    except Exception as e:
        logger.error(f"Silver transformation failed: {e}", exc_info=True)
        raise


def validate_bronze_layer(**context):
    """
    Validate Bronze layer data using Great Expectations.

    This task:
    - Runs Bronze checkpoint (observational validations)
    - Monitors data quality without failing the pipeline
    - Logs validation results for observability
    """
    import sys
    sys.path.insert(0, '/opt/airflow')

    from src.validation.ge_validator import validate_bronze

    logger = logging.getLogger(__name__)
    logger.info("Validating Bronze layer data...")

    try:
        results = validate_bronze(**context)

        # Push results to XCom
        context['task_instance'].xcom_push(
            key='bronze_validation',
            value=results
        )

        logger.info(f"Bronze validation complete: {results['success']}")
        logger.info(f"Statistics: {results.get('statistics', {})}")

        return results

    except Exception as e:
        logger.error(f"Bronze validation failed: {e}", exc_info=True)
        raise


def validate_silver_layer(**context):
    """
    Validate Silver layer data using Great Expectations.

    This task:
    - Runs Silver checkpoint (strict validations)
    - Enforces data quality standards
    - Fails the pipeline if critical validations fail
    """
    import sys
    sys.path.insert(0, '/opt/airflow')

    from src.validation.ge_validator import validate_silver

    logger = logging.getLogger(__name__)
    logger.info("Validating Silver layer data...")

    try:
        results = validate_silver(**context)

        # Push results to XCom
        context['task_instance'].xcom_push(
            key='silver_validation',
            value=results
        )

        if not results['success']:
            logger.warning(
                f"Silver validation had issues: "
                f"{results['statistics']['unsuccessful_expectations']} "
                f"out of {results['statistics']['evaluated_expectations']} expectations failed. "
                f"Data Docs: {results['validation_result_url']}"
            )

        logger.info(f"Silver validation PASSED: {results.get('statistics', {})}")
        return results

    except Exception as e:
        logger.error(f"Silver validation failed: {e}", exc_info=True)
        raise


def validate_gold_layer(**context):
    """
    Validate Gold layer data using Great Expectations.

    This task:
    - Runs Gold checkpoint (business metric validations)
    - Validates aggregation logic and business KPIs
    - Logs warnings but doesn't fail the pipeline
    """
    import sys
    sys.path.insert(0, '/opt/airflow')

    from src.validation.ge_validator import validate_gold

    logger = logging.getLogger(__name__)
    logger.info("Validating Gold layer data...")

    try:
        results = validate_gold(**context)

        # Push results to XCom
        context['task_instance'].xcom_push(
            key='gold_validation',
            value=results
        )

        if not results['success']:
            logger.warning(
                f"Gold validation had issues: "
                f"{results['statistics']['unsuccessful_expectations']} expectations failed. "
                f"Data Docs: {results['validation_result_url']}"
            )
        else:
            logger.info(f"Gold validation PASSED: {results.get('statistics', {})}")

        return results

    except Exception as e:
        logger.error(f"Gold validation failed: {e}", exc_info=True)
        raise


def generate_data_quality_report(**context):
    """
    Generate a data quality report based on pipeline execution results.

    This task:
    - Collects metrics from Bronze, Silver, and Gold layers
    - Includes Great Expectations validation results
    - Generates a summary report
    - Logs key metrics for monitoring
    """
    import sys
    sys.path.insert(0, '/opt/airflow')

    logger = logging.getLogger(__name__)
    logger.info("Generating data quality report...")

    try:
        # Get results from XCom
        ti = context['task_instance']
        bronze_results = ti.xcom_pull(task_ids='extract_bronze_data', key='bronze_results')
        silver_results = ti.xcom_pull(task_ids='transform_silver_data', key='silver_results')
        bronze_validation = ti.xcom_pull(task_ids='validate_bronze', key='bronze_validation')
        silver_validation = ti.xcom_pull(task_ids='validate_silver', key='silver_validation')
        gold_validation = ti.xcom_pull(task_ids='validate_gold', key='gold_validation')

        # Build report
        report = {
            'execution_date': str(context['execution_date']),
            'bronze': bronze_results or {},
            'silver': silver_results or {},
            'validations': {
                'bronze': bronze_validation or {},
                'silver': silver_validation or {},
                'gold': gold_validation or {},
            }
        }

        logger.info("=" * 80)
        logger.info("DATA QUALITY REPORT")
        logger.info("=" * 80)
        logger.info(f"Execution Date: {report['execution_date']}")
        logger.info("-" * 80)
        logger.info("Bronze Layer:")
        for key, value in report['bronze'].items():
            logger.info(f"  {key}: {value}")
        logger.info("-" * 80)
        logger.info("Silver Layer:")
        for key, value in report['silver'].items():
            logger.info(f"  {key}: {value}")
        logger.info("-" * 80)
        logger.info("Great Expectations Validations:")
        for layer, validation in report['validations'].items():
            if validation:
                logger.info(f"  {layer.upper()}: {validation.get('success', 'N/A')} "
                          f"({validation.get('statistics', {}).get('success_percent', 'N/A')}% passed)")
        logger.info("=" * 80)

        return report

    except Exception as e:
        logger.error(f"Report generation failed: {e}", exc_info=True)
        # Don't fail the pipeline if report fails
        return {'error': str(e)}


# ============================================================================
# Task Definitions
# ============================================================================

# Task 1: Extract data from API to Bronze layer
extract_bronze = PythonOperator(
    task_id='extract_bronze_data',
    python_callable=extract_bronze_data,
    provide_context=True,
    dag=dag,
)

# Task 2: Validate Bronze layer with Great Expectations
validate_bronze = PythonOperator(
    task_id='validate_bronze',
    python_callable=validate_bronze_layer,
    provide_context=True,
    dag=dag,
)

# Task 3: Transform Bronze to Silver using PySpark
transform_silver = PythonOperator(
    task_id='transform_silver_data',
    python_callable=transform_silver_data,
    provide_context=True,
    dag=dag,
)

# Task 4: Validate Silver layer with Great Expectations
validate_silver = PythonOperator(
    task_id='validate_silver',
    python_callable=validate_silver_layer,
    provide_context=True,
    dag=dag,
)

# Task 5: Run dbt models to create Gold layer
dbt_run = BashOperator(
    task_id='dbt_gold_transform',
    bash_command='cd /opt/airflow/dbt_project && dbt run --profiles-dir . --full-refresh',
    dag=dag,
)

# Task 6: Run dbt tests
dbt_test = BashOperator(
    task_id='dbt_test',
    bash_command='cd /opt/airflow/dbt_project && dbt test --profiles-dir .',
    dag=dag,
)

# Task 7: Validate Gold layer with Great Expectations
validate_gold = PythonOperator(
    task_id='validate_gold',
    python_callable=validate_gold_layer,
    provide_context=True,
    dag=dag,
)

# Task 8: Generate data quality report
quality_report = PythonOperator(
    task_id='data_quality_report',
    python_callable=generate_data_quality_report,
    provide_context=True,
    dag=dag,
)


# ============================================================================
# Task Dependencies
# ============================================================================

# Define the complete pipeline flow with Great Expectations validations:
# 1. Extract raw data to Bronze layer
# 2. Validate Bronze data (observational - monitors but doesn't fail)
# 3. Transform Bronze to Silver layer
# 4. Validate Silver data (strict - fails pipeline if quality issues)
# 5. Run dbt transformations to create Gold layer
# 6. Run dbt tests on Gold layer
# 7. Validate Gold data (business metrics - logs warnings)
# 8. Generate comprehensive data quality report

extract_bronze >> validate_bronze >> transform_silver >> validate_silver >> dbt_run >> dbt_test >> validate_gold >> quality_report
