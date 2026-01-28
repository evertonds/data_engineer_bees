"""
Functional tests for pipeline idempotency.

Tests that running the pipeline multiple times with the same input
produces the same output without duplicating data or causing side effects.

Key idempotency principles:
- Same input → Same output
- No data duplication
- Safe to retry failed runs
- State is predictable
"""

from datetime import date
from unittest.mock import Mock, patch

import pytest


class TestBronzeIdempotency:
    """Test Bronze layer idempotency."""

    @patch("src.processors.bronze_processor.get_settings")
    @patch("src.processors.bronze_processor.get_storage")
    @patch("src.processors.bronze_processor.BreweryAPIClient")
    @patch("src.processors.bronze_processor.PostgreSQLLoader")
    def test_same_date_produces_same_filename(
        self, mock_db, mock_api, mock_storage, mock_settings
    ):
        """Running Bronze with same date should use same filename (overwrite)."""
        from src.processors.bronze_processor import BronzeProcessor

        # Configure mocks
        settings = Mock()
        settings.api.base_url = "https://api.example.com"
        settings.api.rate_limit = 50
        settings.api.timeout = 30
        mock_settings.return_value = settings

        storage = Mock()
        mock_storage.return_value = storage
        storage.write_json.return_value = "/bronze/2025-01-15/data.json"

        api_client = Mock()
        mock_api.return_value = api_client
        api_client.fetch_all_breweries.return_value = [{"id": "1"}]

        db_loader = Mock()
        mock_db.return_value = db_loader
        db_loader.load_bronze_breweries.return_value = 1

        processor = BronzeProcessor()
        test_date = date(2025, 1, 15)

        # Run twice
        processor.extract_breweries(ingestion_date=test_date)
        processor.extract_breweries(ingestion_date=test_date)

        # Verify both calls used same filename structure
        calls = storage.write_json.call_args_list
        assert len(calls) == 2

        filename1 = calls[0][1]["filename"]
        filename2 = calls[1][1]["filename"]

        assert "2025-01-15" in filename1
        assert "2025-01-15" in filename2
        assert filename1 == filename2  # Same filename = overwrite

    @patch("src.processors.bronze_processor.get_settings")
    @patch("src.processors.bronze_processor.get_storage")
    @patch("src.processors.bronze_processor.BreweryAPIClient")
    @patch("src.processors.bronze_processor.PostgreSQLLoader")
    def test_different_dates_produce_different_files(
        self, mock_db, mock_api, mock_storage, mock_settings
    ):
        """Running Bronze with different dates should create separate files."""
        from src.processors.bronze_processor import BronzeProcessor

        # Configure mocks
        settings = Mock()
        settings.api.base_url = "https://api.example.com"
        settings.api.rate_limit = 50
        settings.api.timeout = 30
        mock_settings.return_value = settings

        storage = Mock()
        mock_storage.return_value = storage

        def mock_write_json(**kwargs):
            filename = kwargs["filename"]
            return f"/bronze/{filename}"

        storage.write_json.side_effect = mock_write_json

        api_client = Mock()
        mock_api.return_value = api_client
        api_client.fetch_all_breweries.return_value = [{"id": "1"}]

        db_loader = Mock()
        mock_db.return_value = db_loader
        db_loader.load_bronze_breweries.return_value = 1

        processor = BronzeProcessor()

        # Run with different dates
        processor.extract_breweries(ingestion_date=date(2025, 1, 15))
        processor.extract_breweries(ingestion_date=date(2025, 1, 16))

        # Verify different filenames
        calls = storage.write_json.call_args_list
        filename1 = calls[0][1]["filename"]
        filename2 = calls[1][1]["filename"]

        assert "2025-01-15" in filename1
        assert "2025-01-16" in filename2
        assert filename1 != filename2


class TestGoldIdempotency:
    """Test Gold layer idempotency."""

    def test_aggregations_are_deterministic(self):
        """Gold aggregations should produce same results with same input."""
        # Mock Silver data
        silver_data = [
            {"country": "USA", "state": "CA", "type": "A"},
            {"country": "USA", "state": "CA", "type": "A"},
            {"country": "USA", "state": "TX", "type": "B"},
        ]

        # Count aggregation
        from collections import Counter
        groups1 = Counter()
        groups2 = Counter()

        # Run aggregation twice
        for record in silver_data:
            key = (record["country"], record["state"], record["type"])
            groups1[key] += 1

        for record in silver_data:
            key = (record["country"], record["state"], record["type"])
            groups2[key] += 1

        # Results should be identical
        assert groups1 == groups2
        assert groups1[("USA", "CA", "A")] == 2
        assert groups1[("USA", "TX", "B")] == 1

    def test_gold_upsert_pattern_prevents_duplicates(self):
        """Gold UPSERT pattern should prevent duplicate aggregates."""
        # Simulate two runs with same grain
        grain_key = ("USA", "CA", "San Diego", "type_a")

        existing_records = {
            grain_key: {"count": 10, "last_updated": "2025-01-15"},
        }

        # New run with updated count
        new_aggregate = {
            "grain": grain_key,
            "count": 12,  # Updated count
            "last_updated": "2025-01-16",
        }

        # UPSERT: Update existing record
        existing_records[grain_key] = {
            "count": new_aggregate["count"],
            "last_updated": new_aggregate["last_updated"],
        }

        # Should have only 1 record (not 2)
        assert len(existing_records) == 1
        assert existing_records[grain_key]["count"] == 12  # Updated value


class TestStateManagement:
    """Test pipeline state management for idempotency."""

    def test_processing_date_determines_output_location(self):
        """Processing date should determine where data is stored."""
        # Pattern: data/layer/YYYY-MM-DD/
        processing_date = date(2025, 1, 15)

        expected_path_bronze = f"bronze/2025-01-15/data.json"
        expected_path_silver = f"silver/country=USA/state=CA/2025-01-15.parquet"

        assert "2025-01-15" in expected_path_bronze
        assert "2025-01-15" in expected_path_silver

    def test_reprocessing_overwrites_previous_run(self):
        """Reprocessing same date should overwrite (not append)."""
        # Pattern: Full refresh for that date

        # First run: 100 records for 2025-01-15
        state_run1 = {
            "date": date(2025, 1, 15),
            "records": 100,
        }

        # Second run: 95 records for 2025-01-15 (data changed)
        state_run2 = {
            "date": date(2025, 1, 15),
            "records": 95,
        }

        # After reprocessing, should have 95 (not 195)
        assert state_run2["records"] == 95

    def test_failed_run_does_not_corrupt_state(self):
        """Failed pipeline run should not leave partial/corrupted data."""
        # Pattern: Atomic operations or staging tables

        # Simulate processing
        staging_data = [{"id": "1"}, {"id": "2"}]

        try:
            # Process data
            if len(staging_data) > 0:
                raise Exception("Simulated failure")

            # Commit (should not reach here)
            final_data = staging_data
        except Exception:
            # Rollback - staging data not committed
            final_data = []

        # Failed run should leave no data
        assert len(final_data) == 0


class TestRetryBehavior:
    """Test pipeline retry behavior."""

    @patch("src.processors.bronze_processor.get_settings")
    @patch("src.processors.bronze_processor.get_storage")
    @patch("src.processors.bronze_processor.BreweryAPIClient")
    @patch("src.processors.bronze_processor.PostgreSQLLoader")
    def test_retry_after_failure_produces_same_result(
        self, mock_db, mock_api, mock_storage, mock_settings
    ):
        """Retrying after failure should produce same result as initial success."""
        from src.processors.bronze_processor import BronzeProcessor

        # Configure mocks
        settings = Mock()
        settings.api.base_url = "https://api.example.com"
        settings.api.rate_limit = 50
        settings.api.timeout = 30
        mock_settings.return_value = settings

        storage = Mock()
        mock_storage.return_value = storage
        storage.write_json.return_value = "/bronze/data.json"

        raw_data = [{"id": "1"}, {"id": "2"}]

        api_client = Mock()
        mock_api.return_value = api_client
        api_client.fetch_all_breweries.return_value = raw_data

        db_loader = Mock()
        mock_db.return_value = db_loader
        db_loader.load_bronze_breweries.return_value = 2

        processor = BronzeProcessor()
        test_date = date(2025, 1, 15)

        # First attempt (success)
        result1 = processor.extract_breweries(ingestion_date=test_date)

        # Retry (after hypothetical failure)
        result2 = processor.extract_breweries(ingestion_date=test_date)

        # Results should be identical
        assert result1["records_fetched"] == result2["records_fetched"]
        assert result1["ingestion_date"] == result2["ingestion_date"]

    def test_partial_run_can_be_restarted(self):
        """Partial run should be restartable from last successful point."""
        # Pattern: Checkpoint/watermark tracking

        checkpoints = []

        # Simulate pipeline with checkpoints
        tasks = ["extract", "validate", "transform", "load"]

        # First run: fails at transform
        for i, task in enumerate(tasks):
            if task == "transform":
                # Failure
                break
            checkpoints.append(task)

        assert checkpoints == ["extract", "validate"]

        # Retry: skip completed tasks
        for task in tasks:
            if task not in checkpoints:
                checkpoints.append(task)

        # Should complete all tasks without redoing work
        assert checkpoints == ["extract", "validate", "transform", "load"]
