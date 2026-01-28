"""
Unit tests for Bronze Layer architectural pattern.

Tests the Bronze layer behavior independent of domain (breweries).
Validates:
- Schema-on-read pattern (accepts any data structure)
- Raw data persistence without transformation
- Metadata enrichment (timestamps, dates)
- Storage abstraction
"""

from datetime import date, datetime
from unittest.mock import Mock, patch

import pytest

from src.processors.bronze_processor import BronzeProcessor


@pytest.fixture
def mock_dependencies():
    """Mock Bronze processor dependencies."""
    with patch("src.processors.bronze_processor.get_settings") as mock_settings, \
         patch("src.processors.bronze_processor.get_storage") as mock_storage, \
         patch("src.processors.bronze_processor.BreweryAPIClient") as mock_api_client, \
         patch("src.processors.bronze_processor.PostgreSQLLoader") as mock_db_loader:

        settings = Mock()
        settings.api.base_url = "https://api.example.com"
        settings.api.rate_limit = 50
        settings.api.timeout = 30
        mock_settings.return_value = settings

        storage = Mock()
        mock_storage.return_value = storage

        api_client = Mock()
        mock_api_client.return_value = api_client

        db_loader = Mock()
        mock_db_loader.return_value = db_loader

        yield {
            "settings": settings,
            "storage": storage,
            "api_client": api_client,
            "db_loader": db_loader,
        }


@pytest.fixture
def processor(mock_dependencies):
    """Create Bronze processor instance."""
    return BronzeProcessor()


class TestSchemaOnReadPattern:
    """Test that Bronze layer accepts any data structure (schema-on-read)."""

    def test_accepts_minimal_structure(self, processor, mock_dependencies):
        """Bronze should accept data with minimal fields."""
        minimal_data = [{"id": "1", "name": "Item 1"}]

        mock_dependencies["api_client"].fetch_all_breweries.return_value = minimal_data
        mock_dependencies["storage"].write_json.return_value = "/path/to/file"
        mock_dependencies["db_loader"].load_bronze_breweries.return_value = 1

        result = processor.extract_breweries()

        assert result["status"] == "success"
        assert result["records_fetched"] == 1

    def test_accepts_extended_structure(self, processor, mock_dependencies):
        """Bronze should accept data with extra fields."""
        extended_data = [
            {
                "id": "1",
                "name": "Item 1",
                "extra_field_1": "value1",
                "extra_field_2": 123,
                "nested": {"key": "value"},
            }
        ]

        mock_dependencies["api_client"].fetch_all_breweries.return_value = extended_data
        mock_dependencies["storage"].write_json.return_value = "/path/to/file"
        mock_dependencies["db_loader"].load_bronze_breweries.return_value = 1

        result = processor.extract_breweries()

        assert result["status"] == "success"
        # Bronze accepts any structure without validation

    def test_accepts_different_data_types(self, processor, mock_dependencies):
        """Bronze should accept various data types without type validation."""
        mixed_data = [
            {"id": 1, "name": "String name"},
            {"id": "uuid-123", "name": 999},
            {"id": None, "name": None},
        ]

        mock_dependencies["api_client"].fetch_all_breweries.return_value = mixed_data
        mock_dependencies["storage"].write_json.return_value = "/path/to/file"
        mock_dependencies["db_loader"].load_bronze_breweries.return_value = 3

        result = processor.extract_breweries()

        assert result["status"] == "success"
        assert result["records_fetched"] == 3


class TestRawDataPersistence:
    """Test that Bronze layer persists raw data without transformation."""

    def test_data_persisted_unchanged(self, processor, mock_dependencies):
        """Raw data should be persisted exactly as received."""
        original_data = [
            {"id": "1", "field": "  untrimmed  ", "number": "123"}
        ]

        mock_dependencies["api_client"].fetch_all_breweries.return_value = original_data
        mock_dependencies["storage"].write_json.return_value = "/path/to/file"
        mock_dependencies["db_loader"].load_bronze_breweries.return_value = 1

        processor.extract_breweries()

        # Verify storage was called with original data (no transformation)
        call_args = mock_dependencies["storage"].write_json.call_args
        persisted_data = call_args[1]["data"]

        assert persisted_data == original_data
        assert persisted_data[0]["field"] == "  untrimmed  "  # Whitespace preserved
        assert persisted_data[0]["number"] == "123"  # Type preserved

    def test_no_data_cleaning(self, processor, mock_dependencies):
        """Bronze should not clean or validate data."""
        dirty_data = [
            {"id": "", "field": None, "invalid": "###"},
            {"id": "duplicate", "field": "value"},
            {"id": "duplicate", "field": "value"},  # Duplicate allowed
        ]

        mock_dependencies["api_client"].fetch_all_breweries.return_value = dirty_data
        mock_dependencies["storage"].write_json.return_value = "/path/to/file"
        mock_dependencies["db_loader"].load_bronze_breweries.return_value = 3

        result = processor.extract_breweries()

        # All records accepted, including duplicates and invalid data
        assert result["records_fetched"] == 3
        assert result["records_stored"] == 3


class TestMetadataEnrichment:
    """Test that Bronze layer adds ingestion metadata."""

    def test_adds_ingestion_timestamp(self, processor, mock_dependencies):
        """Bronze should add ingestion timestamp to metadata."""
        test_data = [{"id": "1"}]

        mock_dependencies["api_client"].fetch_all_breweries.return_value = test_data
        mock_dependencies["storage"].write_json.return_value = "/path/to/file"
        mock_dependencies["db_loader"].load_bronze_breweries.return_value = 1

        before = datetime.now()
        result = processor.extract_breweries()
        after = datetime.now()

        # Verify ingestion_date is set
        assert "ingestion_date" in result
        ingestion_date = datetime.strptime(result["ingestion_date"], "%Y-%m-%d").date()
        assert before.date() <= ingestion_date <= after.date()

    def test_uses_provided_ingestion_date(self, processor, mock_dependencies):
        """Bronze should use provided ingestion date when specified."""
        test_data = [{"id": "1"}]
        custom_date = date(2025, 1, 15)

        mock_dependencies["api_client"].fetch_all_breweries.return_value = test_data
        mock_dependencies["storage"].write_json.return_value = "/path/to/file"
        mock_dependencies["db_loader"].load_bronze_breweries.return_value = 1

        result = processor.extract_breweries(ingestion_date=custom_date)

        assert result["ingestion_date"] == "2025-01-15"

    def test_filename_includes_date_partition(self, processor, mock_dependencies):
        """Bronze should store data in date-partitioned structure."""
        test_data = [{"id": "1"}]
        ingestion_date = date(2025, 1, 24)

        mock_dependencies["api_client"].fetch_all_breweries.return_value = test_data
        mock_dependencies["storage"].write_json.return_value = "/path/to/file"
        mock_dependencies["db_loader"].load_bronze_breweries.return_value = 1

        processor.extract_breweries(ingestion_date=ingestion_date)

        # Verify filename contains date partition
        call_args = mock_dependencies["storage"].write_json.call_args
        filename = call_args[1]["filename"]
        assert "2025-01-24" in filename


class TestStorageAbstraction:
    """Test Bronze layer storage abstraction."""

    def test_writes_to_correct_layer(self, processor, mock_dependencies):
        """Bronze should write to 'bronze' layer."""
        test_data = [{"id": "1"}]

        mock_dependencies["api_client"].fetch_all_breweries.return_value = test_data
        mock_dependencies["storage"].write_json.return_value = "/path/to/file"
        mock_dependencies["db_loader"].load_bronze_breweries.return_value = 1

        processor.extract_breweries()

        call_args = mock_dependencies["storage"].write_json.call_args
        assert call_args[1]["layer"] == "bronze"

    def test_writes_to_correct_dataset(self, processor, mock_dependencies):
        """Bronze should write to dataset namespace."""
        test_data = [{"id": "1"}]

        mock_dependencies["api_client"].fetch_all_breweries.return_value = test_data
        mock_dependencies["storage"].write_json.return_value = "/path/to/file"
        mock_dependencies["db_loader"].load_bronze_breweries.return_value = 1

        processor.extract_breweries()

        call_args = mock_dependencies["storage"].write_json.call_args
        assert call_args[1]["dataset"] == "breweries"

    def test_storage_path_returned(self, processor, mock_dependencies):
        """Bronze should return storage path after persistence."""
        test_data = [{"id": "1"}]
        expected_path = "/bronze/dataset/2025-01-24/data.json"

        mock_dependencies["api_client"].fetch_all_breweries.return_value = test_data
        mock_dependencies["storage"].write_json.return_value = expected_path
        mock_dependencies["db_loader"].load_bronze_breweries.return_value = 1

        result = processor.extract_breweries()

        assert result["storage_path"] == expected_path


class TestDualPersistence:
    """Test that Bronze persists to both storage and database."""

    def test_writes_to_storage_and_database(self, processor, mock_dependencies):
        """Bronze should persist data to both storage (files) and database."""
        test_data = [{"id": "1"}, {"id": "2"}]

        mock_dependencies["api_client"].fetch_all_breweries.return_value = test_data
        mock_dependencies["storage"].write_json.return_value = "/path/to/file"
        mock_dependencies["db_loader"].load_bronze_breweries.return_value = 2

        processor.extract_breweries()

        # Verify both storage and database were called
        mock_dependencies["storage"].write_json.assert_called_once()
        mock_dependencies["db_loader"].load_bronze_breweries.assert_called_once_with(test_data)

    def test_database_load_count_tracked(self, processor, mock_dependencies):
        """Bronze should track number of records loaded to database."""
        test_data = [{"id": str(i)} for i in range(100)]

        mock_dependencies["api_client"].fetch_all_breweries.return_value = test_data
        mock_dependencies["storage"].write_json.return_value = "/path/to/file"
        mock_dependencies["db_loader"].load_bronze_breweries.return_value = 100

        result = processor.extract_breweries()

        assert result["records_loaded_db"] == 100


class TestEmptyDataHandling:
    """Test Bronze layer behavior with empty datasets."""

    def test_handles_empty_response(self, processor, mock_dependencies):
        """Bronze should handle empty API response gracefully."""
        mock_dependencies["api_client"].fetch_all_breweries.return_value = []

        result = processor.extract_breweries()

        # Should not write to storage or database
        mock_dependencies["storage"].write_json.assert_not_called()
        mock_dependencies["db_loader"].load_bronze_breweries.assert_not_called()

        assert result["status"] == "success"
        assert result["records_fetched"] == 0
        assert result["records_stored"] == 0
        assert result["records_loaded_db"] == 0

    def test_returns_success_on_empty(self, processor, mock_dependencies):
        """Empty dataset should still return success status."""
        mock_dependencies["api_client"].fetch_all_breweries.return_value = []

        result = processor.extract_breweries()

        assert result["status"] == "success"
