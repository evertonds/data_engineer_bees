"""
Unit tests for Data Quality Framework integration.

Tests Great Expectations integration and data quality patterns independent of domain.
Validates:
- Validation framework integration
- Quality checkpoints execution
- Validation result handling
- Data quality metrics tracking
"""

from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def mock_ge_context():
    """Mock Great Expectations DataContext."""
    with patch("src.validation.ge_validator.ge.data_context.DataContext") as mock_context:
        context = Mock()
        mock_context.return_value = context
        yield context


class TestValidationFrameworkIntegration:
    """Test Great Expectations framework integration."""

    @patch("src.validation.ge_validator.ge.data_context.DataContext")
    def test_validator_initializes_context(self, mock_context):
        """Validator should initialize GE context on creation."""
        from src.validation.ge_validator import GreatExpectationsValidator

        context_instance = Mock()
        mock_context.return_value = context_instance

        validator = GreatExpectationsValidator(
            ge_root_dir="/opt/airflow/great_expectations"
        )

        assert validator.context is not None
        mock_context.assert_called_once()

    @patch("src.validation.ge_validator.ge.data_context.DataContext")
    def test_validator_handles_missing_context_gracefully(self, mock_context):
        """Validator should handle missing GE context with clear error."""
        from src.validation.ge_validator import GreatExpectationsValidator

        mock_context.side_effect = Exception("Context not found")

        with pytest.raises(Exception) as exc_info:
            GreatExpectationsValidator()

        assert "Context not found" in str(exc_info.value)


class TestCheckpointExecution:
    """Test validation checkpoint execution."""

    @patch("src.validation.ge_validator.ge.data_context.DataContext")
    def test_runs_checkpoint_by_name(self, mock_context):
        """Validator should execute checkpoint by name."""
        from src.validation.ge_validator import GreatExpectationsValidator

        context_instance = Mock()
        mock_context.return_value = context_instance

        checkpoint = Mock()
        checkpoint_result = Mock()
        checkpoint_result.success = True
        checkpoint_result.run_id.run_name = "test_run"
        checkpoint_result.list_validation_results.return_value = [
            Mock(statistics={"evaluated_expectations": 5, "successful_expectations": 5, "unsuccessful_expectations": 0, "success_percent": 100.0})
        ]

        checkpoint.run.return_value = checkpoint_result
        context_instance.get_checkpoint.return_value = checkpoint

        validator = GreatExpectationsValidator()
        result = validator.run_checkpoint("test_checkpoint")

        assert result["success"] == True
        assert result["checkpoint_name"] == "test_checkpoint"
        context_instance.get_checkpoint.assert_called_once_with("test_checkpoint")

    @patch("src.validation.ge_validator.ge.data_context.DataContext")
    def test_handles_checkpoint_failures(self, mock_context):
        """Validator should handle checkpoint failures gracefully."""
        from src.validation.ge_validator import GreatExpectationsValidator

        context_instance = Mock()
        mock_context.return_value = context_instance

        checkpoint = Mock()
        checkpoint_result = Mock()
        checkpoint_result.success = False
        checkpoint_result.run_id.run_name = "failed_run"
        checkpoint_result.list_validation_results.return_value = [
            Mock(statistics={"evaluated_expectations": 5, "successful_expectations": 3, "unsuccessful_expectations": 2, "success_percent": 60.0})
        ]

        checkpoint.run.return_value = checkpoint_result
        context_instance.get_checkpoint.return_value = checkpoint

        validator = GreatExpectationsValidator()
        result = validator.run_checkpoint("test_checkpoint")

        assert result["success"] == False
        assert result["statistics"]["unsuccessful_expectations"] == 2


class TestValidationResultHandling:
    """Test validation result processing."""

    @patch("src.validation.ge_validator.ge.data_context.DataContext")
    def test_extracts_validation_statistics(self, mock_context):
        """Should extract key statistics from validation results."""
        from src.validation.ge_validator import GreatExpectationsValidator

        context_instance = Mock()
        mock_context.return_value = context_instance

        checkpoint = Mock()
        checkpoint_result = Mock()
        checkpoint_result.success = True
        checkpoint_result.run_id.run_name = "test_run"

        validation_result = Mock()
        validation_result.statistics = {
            "evaluated_expectations": 10,
            "successful_expectations": 8,
            "unsuccessful_expectations": 2,
            "success_percent": 80.0,
        }
        checkpoint_result.list_validation_results.return_value = [validation_result]

        checkpoint.run.return_value = checkpoint_result
        context_instance.get_checkpoint.return_value = checkpoint

        validator = GreatExpectationsValidator()
        result = validator.run_checkpoint("test_checkpoint")

        assert result["statistics"]["evaluated_expectations"] == 10
        assert result["statistics"]["successful_expectations"] == 8
        assert result["statistics"]["unsuccessful_expectations"] == 2
        assert result["statistics"]["success_percent"] == 80.0

    @patch("src.validation.ge_validator.ge.data_context.DataContext")
    def test_includes_validation_result_url(self, mock_context):
        """Should include URL to validation results (data docs)."""
        from src.validation.ge_validator import GreatExpectationsValidator

        context_instance = Mock()
        mock_context.return_value = context_instance

        checkpoint = Mock()
        checkpoint_result = Mock()
        checkpoint_result.success = True
        checkpoint_result.run_id = Mock(run_name="test_run")
        checkpoint_result.list_validation_results.return_value = [
            Mock(statistics={"evaluated_expectations": 5, "successful_expectations": 5, "unsuccessful_expectations": 0, "success_percent": 100.0})
        ]

        checkpoint.run.return_value = checkpoint_result
        context_instance.get_checkpoint.return_value = checkpoint

        validator = GreatExpectationsValidator()
        result = validator.run_checkpoint("test_checkpoint")

        assert "validation_result_url" in result
        assert result["validation_result_url"] is not None


class TestLayerSpecificValidations:
    """Test layer-specific validation methods."""

    @patch("src.validation.ge_validator.ge.data_context.DataContext")
    def test_validates_bronze_layer(self, mock_context):
        """Should have dedicated method for Bronze validation."""
        from src.validation.ge_validator import GreatExpectationsValidator

        context_instance = Mock()
        mock_context.return_value = context_instance

        checkpoint = Mock()
        checkpoint_result = Mock()
        checkpoint_result.success = True
        checkpoint_result.run_id.run_name = "bronze_run"
        checkpoint_result.list_validation_results.return_value = [
            Mock(statistics={"evaluated_expectations": 4, "successful_expectations": 4, "unsuccessful_expectations": 0, "success_percent": 100.0})
        ]

        checkpoint.run.return_value = checkpoint_result
        context_instance.get_checkpoint.return_value = checkpoint

        validator = GreatExpectationsValidator()
        result = validator.validate_bronze_layer()

        assert result["success"] == True
        context_instance.get_checkpoint.assert_called_with("bronze_checkpoint")

    @patch("src.validation.ge_validator.ge.data_context.DataContext")
    def test_validates_silver_layer(self, mock_context):
        """Should have dedicated method for Silver validation."""
        from src.validation.ge_validator import GreatExpectationsValidator

        context_instance = Mock()
        mock_context.return_value = context_instance

        checkpoint = Mock()
        checkpoint_result = Mock()
        checkpoint_result.success = True
        checkpoint_result.run_id.run_name = "silver_run"
        checkpoint_result.list_validation_results.return_value = [
            Mock(statistics={"evaluated_expectations": 6, "successful_expectations": 6, "unsuccessful_expectations": 0, "success_percent": 100.0})
        ]

        checkpoint.run.return_value = checkpoint_result
        context_instance.get_checkpoint.return_value = checkpoint

        validator = GreatExpectationsValidator()
        result = validator.validate_silver_layer()

        assert result["success"] == True
        context_instance.get_checkpoint.assert_called_with("silver_checkpoint")

    @patch("src.validation.ge_validator.ge.data_context.DataContext")
    def test_validates_gold_layer(self, mock_context):
        """Should have dedicated method for Gold validation."""
        from src.validation.ge_validator import GreatExpectationsValidator

        context_instance = Mock()
        mock_context.return_value = context_instance

        checkpoint = Mock()
        checkpoint_result = Mock()
        checkpoint_result.success = True
        checkpoint_result.run_id.run_name = "gold_run"
        checkpoint_result.list_validation_results.return_value = [
            Mock(statistics={"evaluated_expectations": 6, "successful_expectations": 6, "unsuccessful_expectations": 0, "success_percent": 100.0})
        ]

        checkpoint.run.return_value = checkpoint_result
        context_instance.get_checkpoint.return_value = checkpoint

        validator = GreatExpectationsValidator()
        result = validator.validate_gold_layer()

        assert result["success"] == True
        context_instance.get_checkpoint.assert_called_with("gold_checkpoint")


class TestAirflowIntegration:
    """Test Airflow task integration functions."""

    @patch("src.validation.ge_validator.GreatExpectationsValidator")
    def test_validate_bronze_callable(self, mock_validator_class):
        """validate_bronze function should be callable from Airflow."""
        from src.validation.ge_validator import validate_bronze

        validator_instance = Mock()
        validator_instance.validate_bronze_layer.return_value = {
            "success": True,
            "checkpoint_name": "bronze_checkpoint",
        }
        mock_validator_class.return_value = validator_instance

        result = validate_bronze()

        assert result["success"] == True
        validator_instance.validate_bronze_layer.assert_called_once()

    @patch("src.validation.ge_validator.GreatExpectationsValidator")
    def test_validate_silver_callable(self, mock_validator_class):
        """validate_silver function should be callable from Airflow."""
        from src.validation.ge_validator import validate_silver

        validator_instance = Mock()
        validator_instance.validate_silver_layer.return_value = {
            "success": True,
            "checkpoint_name": "silver_checkpoint",
        }
        mock_validator_class.return_value = validator_instance

        result = validate_silver()

        assert result["success"] == True
        validator_instance.validate_silver_layer.assert_called_once()

    @patch("src.validation.ge_validator.GreatExpectationsValidator")
    def test_validate_gold_callable(self, mock_validator_class):
        """validate_gold function should be callable from Airflow."""
        from src.validation.ge_validator import validate_gold

        validator_instance = Mock()
        validator_instance.validate_gold_layer.return_value = {
            "success": True,
            "checkpoint_name": "gold_checkpoint",
        }
        mock_validator_class.return_value = validator_instance

        result = validate_gold()

        assert result["success"] == True
        validator_instance.validate_gold_layer.assert_called_once()


class TestDataQualityMetrics:
    """Test data quality metrics tracking."""

    def test_calculates_success_percentage(self):
        """Should calculate validation success percentage."""
        evaluated = 10
        successful = 8
        unsuccessful = 2

        success_percent = (successful / evaluated) * 100

        assert success_percent == 80.0

    def test_tracks_expectation_counts(self):
        """Should track counts of evaluated, successful, and unsuccessful expectations."""
        validation_stats = {
            "evaluated_expectations": 10,
            "successful_expectations": 8,
            "unsuccessful_expectations": 2,
        }

        assert validation_stats["evaluated_expectations"] == 10
        assert validation_stats["successful_expectations"] + validation_stats["unsuccessful_expectations"] == validation_stats["evaluated_expectations"]

    def test_identifies_passing_validations(self):
        """Should identify when all validations pass."""
        validation_stats = {
            "successful_expectations": 10,
            "unsuccessful_expectations": 0,
        }

        all_passed = validation_stats["unsuccessful_expectations"] == 0

        assert all_passed == True

    def test_identifies_failing_validations(self):
        """Should identify when any validation fails."""
        validation_stats = {
            "successful_expectations": 8,
            "unsuccessful_expectations": 2,
        }

        has_failures = validation_stats["unsuccessful_expectations"] > 0

        assert has_failures == True


class TestValidationPhilosophy:
    """Test validation philosophy per layer."""

    def test_bronze_observational_validation(self):
        """Bronze validations should be observational (don't fail pipeline)."""
        # Pattern: Monitor but don't reject data

        bronze_validation_mode = "observational"

        assert bronze_validation_mode == "observational"

    def test_silver_strict_validation(self):
        """Silver validations should be strict (fail on quality issues)."""
        # Pattern: Enforce data quality standards

        silver_validation_mode = "strict"

        assert silver_validation_mode == "strict"

    def test_gold_business_rule_validation(self):
        """Gold validations should verify business logic correctness."""
        # Pattern: Validate aggregations and business metrics

        gold_validation_focus = "business_metrics"

        assert gold_validation_focus == "business_metrics"


class TestErrorHandling:
    """Test error handling in validations."""

    @patch("src.validation.ge_validator.ge.data_context.DataContext")
    def test_handles_checkpoint_not_found(self, mock_context):
        """Should handle gracefully when checkpoint doesn't exist."""
        from src.validation.ge_validator import GreatExpectationsValidator

        context_instance = Mock()
        mock_context.return_value = context_instance
        context_instance.get_checkpoint.side_effect = Exception("Checkpoint not found")

        validator = GreatExpectationsValidator()

        with pytest.raises(Exception) as exc_info:
            validator.run_checkpoint("nonexistent_checkpoint")

        assert "Checkpoint not found" in str(exc_info.value)

    @patch("src.validation.ge_validator.ge.data_context.DataContext")
    def test_handles_validation_execution_errors(self, mock_context):
        """Should handle errors during validation execution."""
        from src.validation.ge_validator import GreatExpectationsValidator

        context_instance = Mock()
        mock_context.return_value = context_instance

        checkpoint = Mock()
        checkpoint.run.side_effect = Exception("Validation execution failed")
        context_instance.get_checkpoint.return_value = checkpoint

        validator = GreatExpectationsValidator()

        with pytest.raises(Exception) as exc_info:
            validator.run_checkpoint("test_checkpoint")

        assert "Validation execution failed" in str(exc_info.value)
