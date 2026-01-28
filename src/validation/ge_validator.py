"""
Great Expectations Validator
Integrates Great Expectations data validation with Airflow pipeline.
"""

import logging
import os
from pathlib import Path
from typing import Dict, Optional

import great_expectations as ge
from great_expectations.checkpoint import SimpleCheckpoint
from great_expectations.core.batch import RuntimeBatchRequest
from great_expectations.data_context import DataContext
from great_expectations.data_context.types.base import DataContextConfig

logger = logging.getLogger(__name__)


class GreatExpectationsValidator:
    """
    Validator for running Great Expectations checkpoints in Airflow.

    Usage:
        validator = GreatExpectationsValidator()
        result = validator.run_checkpoint("bronze_checkpoint")
        if not result["success"]:
            raise Exception("Validation failed!")
    """

    def __init__(self, ge_root_dir: Optional[str] = None):
        """
        Initialize Great Expectations validator.

        Args:
            ge_root_dir: Path to Great Expectations root directory
                        Defaults to /opt/airflow/great_expectations
        """
        if ge_root_dir is None:
            ge_root_dir = "/opt/airflow/great_expectations"

        self.ge_root_dir = Path(ge_root_dir)
        self.context = self._get_or_create_context()

        logger.info(f"Initialized GE Validator with root: {self.ge_root_dir}")

    def _get_or_create_context(self) -> DataContext:
        """
        Get or create Great Expectations DataContext.

        Returns:
            DataContext instance
        """
        try:
            # Try to load existing context
            context = ge.data_context.DataContext(
                context_root_dir=str(self.ge_root_dir)
            )
            logger.info("Loaded existing Great Expectations context")
            return context
        except Exception as e:
            logger.error(f"Failed to load GE context: {e}")
            raise

    def run_checkpoint(
        self,
        checkpoint_name: str,
        batch_request: Optional[RuntimeBatchRequest] = None
    ) -> Dict:
        """
        Run a Great Expectations checkpoint.

        Args:
            checkpoint_name: Name of the checkpoint to run
            batch_request: Optional batch request (defaults to checkpoint config)

        Returns:
            Dictionary with validation results:
            {
                "success": bool,
                "checkpoint_name": str,
                "run_id": str,
                "validation_result_url": str,
                "statistics": {
                    "evaluated_expectations": int,
                    "successful_expectations": int,
                    "unsuccessful_expectations": int,
                    "success_percent": float
                }
            }

        Raises:
            Exception if checkpoint fails and catch_exceptions is False
        """
        logger.info(f"Running checkpoint: {checkpoint_name}")

        try:
            # Get checkpoint
            checkpoint = self.context.get_checkpoint(checkpoint_name)

            # Run checkpoint
            if batch_request:
                results = checkpoint.run(batch_request=batch_request)
            else:
                results = checkpoint.run()

            # Extract validation results
            validation_result = results.list_validation_results()[0]

            # Calculate statistics from the validation result
            success = results.success

            # Get statistics dictionary from validation result
            stats = validation_result.statistics if hasattr(validation_result, 'statistics') else {}

            # Extract expectation counts
            evaluated = stats.get("evaluated_expectations", 0)
            successful = stats.get("successful_expectations", 0)
            unsuccessful = stats.get("unsuccessful_expectations", 0)
            success_percent = stats.get("success_percent", 0.0)

            result = {
                "success": success,
                "checkpoint_name": checkpoint_name,
                "run_id": results.run_id.run_name,
                "validation_result_url": self._get_data_docs_url(results.run_id),
                "statistics": {
                    "evaluated_expectations": evaluated,
                    "successful_expectations": successful,
                    "unsuccessful_expectations": unsuccessful,
                    "success_percent": success_percent,
                }
            }

            if success:
                logger.info(
                    f"✅ Checkpoint {checkpoint_name} PASSED "
                    f"({stats['successful_expectations']}/{stats['evaluated_expectations']} "
                    f"expectations met)"
                )
            else:
                logger.warning(
                    f"❌ Checkpoint {checkpoint_name} FAILED "
                    f"({stats['unsuccessful_expectations']}/{stats['evaluated_expectations']} "
                    f"expectations failed)"
                )
                logger.warning(f"Data Docs URL: {result['validation_result_url']}")

            return result

        except Exception as e:
            logger.error(f"Failed to run checkpoint {checkpoint_name}: {e}")
            raise

    def validate_bronze_layer(self) -> Dict:
        """
        Validate Bronze layer data.

        Returns:
            Validation results dictionary
        """
        return self.run_checkpoint("bronze_checkpoint")

    def validate_silver_layer(self) -> Dict:
        """
        Validate Silver layer data.

        Returns:
            Validation results dictionary
        """
        return self.run_checkpoint("silver_checkpoint")

    def validate_gold_layer(self) -> Dict:
        """
        Validate Gold layer data.

        Returns:
            Validation results dictionary
        """
        return self.run_checkpoint("gold_checkpoint")

    def _get_data_docs_url(self, run_id) -> str:
        """
        Get Data Docs URL for a validation run.

        Args:
            run_id: Validation run ID

        Returns:
            URL to Data Docs for this validation
        """
        # In local environment, this would be a file:// URL
        # In production, this could be an S3/GCS URL
        data_docs_path = self.ge_root_dir / "uncommitted" / "data_docs" / "local_site"
        return f"file://{data_docs_path}/index.html"

    def get_validation_statistics(self, checkpoint_name: str) -> Dict:
        """
        Get historical statistics for a checkpoint.

        Args:
            checkpoint_name: Name of checkpoint

        Returns:
            Dictionary with historical statistics
        """
        try:
            # Get all validation results for this checkpoint
            validations_store = self.context.stores["validations_store"]

            # This is a simplified version - in production you'd want to
            # aggregate statistics across multiple runs
            logger.info(f"Getting statistics for checkpoint: {checkpoint_name}")

            return {
                "checkpoint_name": checkpoint_name,
                "message": "Historical statistics not yet implemented"
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {}


# Convenience functions for Airflow tasks
def validate_bronze(**context) -> Dict:
    """
    Airflow task function to validate Bronze layer.

    Usage in DAG:
        validate_bronze_task = PythonOperator(
            task_id="validate_bronze",
            python_callable=validate_bronze,
        )
    """
    validator = GreatExpectationsValidator()
    return validator.validate_bronze_layer()


def validate_silver(**context) -> Dict:
    """
    Airflow task function to validate Silver layer.

    Usage in DAG:
        validate_silver_task = PythonOperator(
            task_id="validate_silver",
            python_callable=validate_silver,
        )
    """
    validator = GreatExpectationsValidator()
    return validator.validate_silver_layer()


def validate_gold(**context) -> Dict:
    """
    Airflow task function to validate Gold layer.

    Usage in DAG:
        validate_gold_task = PythonOperator(
            task_id="validate_gold",
            python_callable=validate_gold,
        )
    """
    validator = GreatExpectationsValidator()
    return validator.validate_gold_layer()
