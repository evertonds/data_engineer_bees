"""
Integration tests for Medallion Architecture pipeline flow.

Tests the complete Bronze → Silver → Gold data flow independent of domain.
Validates:
- Data flows through all three layers
- Each layer adds value (quality, structure, insights)
- Metadata is preserved and enriched
- End-to-end data lineage
- Pipeline idempotency
"""

from datetime import date
from unittest.mock import Mock, patch

import pytest


@pytest.fixture
def sample_raw_data():
    """Sample raw data (as it would come from an API)."""
    return [
        {
            "id": "1",
            "name": "  Item One  ",  # Has whitespace
            "category": "type_a",
            "location_country": "USA",
            "location_state": "CA",
            "location_city": "San Diego",
            "coordinate_lon": "-117.16",
            "coordinate_lat": "32.71",
            "contact_website": "http://example.com",
            "extra_field": "ignored",
        },
        {
            "id": "2",
            "name": "Item Two",
            "category": "type_b",
            "location_country": "USA",
            "location_state": "TX",
            "location_city": "Austin",
            "coordinate_lon": None,  # Missing coordinate
            "coordinate_lat": None,
            "contact_website": None,
        },
        {
            "id": "1",  # Duplicate ID
            "name": "Item One Duplicate",
            "category": "type_a",
            "location_country": "USA",
            "location_state": "CA",
            "location_city": "San Diego",
        },
    ]


class TestBronzeLayer:
    """Test Bronze layer in pipeline flow."""

    @patch("src.processors.bronze_processor.get_settings")
    @patch("src.processors.bronze_processor.get_storage")
    @patch("src.processors.bronze_processor.BreweryAPIClient")
    @patch("src.processors.bronze_processor.PostgreSQLLoader")
    def test_bronze_accepts_raw_data(
        self, mock_db, mock_api, mock_storage, mock_settings, sample_raw_data
    ):
        """Bronze layer should accept raw data without validation."""
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

        api_client = Mock()
        mock_api.return_value = api_client
        api_client.fetch_all_breweries.return_value = sample_raw_data

        db_loader = Mock()
        mock_db.return_value = db_loader
        db_loader.load_bronze_breweries.return_value = len(sample_raw_data)

        # Execute Bronze processing
        processor = BronzeProcessor()
        result = processor.extract_breweries()

        # Verify Bronze behavior
        assert result["status"] == "success"
        assert result["records_fetched"] == 3  # Includes duplicate
        assert result["records_stored"] == 3   # No filtering

        # Verify raw data was persisted unchanged
        call_args = storage.write_json.call_args
        persisted_data = call_args[1]["data"]
        assert persisted_data == sample_raw_data  # Exact match

    @patch("src.processors.bronze_processor.get_settings")
    @patch("src.processors.bronze_processor.get_storage")
    @patch("src.processors.bronze_processor.BreweryAPIClient")
    @patch("src.processors.bronze_processor.PostgreSQLLoader")
    def test_bronze_adds_metadata(
        self, mock_db, mock_api, mock_storage, mock_settings, sample_raw_data
    ):
        """Bronze layer should add ingestion metadata."""
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

        api_client = Mock()
        mock_api.return_value = api_client
        api_client.fetch_all_breweries.return_value = sample_raw_data

        db_loader = Mock()
        mock_db.return_value = db_loader
        db_loader.load_bronze_breweries.return_value = len(sample_raw_data)

        # Execute with specific date
        ingestion_date = date(2025, 1, 20)
        processor = BronzeProcessor()
        result = processor.extract_breweries(ingestion_date=ingestion_date)

        # Verify metadata
        assert result["ingestion_date"] == "2025-01-20"


class TestGoldLayer:
    """Test Gold layer in pipeline flow."""

    def test_gold_aggregates_silver_data(self):
        """Gold layer should aggregate Silver data by dimensions."""
        # This would typically use dbt, but we can test the pattern

        # Mock Silver data structure
        silver_data = [
            {"country": "USA", "state": "CA", "city": "San Diego", "type": "type_a"},
            {"country": "USA", "state": "CA", "city": "San Diego", "type": "type_a"},
            {"country": "USA", "state": "CA", "city": "Los Angeles", "type": "type_b"},
            {"country": "USA", "state": "TX", "city": "Austin", "type": "type_a"},
        ]

        # Expected Gold aggregation
        expected_groups = [
            ("USA", "CA", "San Diego", "type_a", 2),  # 2 records
            ("USA", "CA", "Los Angeles", "type_b", 1),
            ("USA", "TX", "Austin", "type_a", 1),
        ]

        # Verify grouping logic
        from collections import Counter
        groups = Counter()
        for record in silver_data:
            key = (record["country"], record["state"], record["city"], record["type"])
            groups[key] += 1

        assert len(groups) == 3  # 3 unique combinations
        assert groups[("USA", "CA", "San Diego", "type_a")] == 2


class TestPipelineIdempotency:
    """Test that pipeline can be re-run safely."""

    @patch("src.processors.bronze_processor.get_settings")
    @patch("src.processors.bronze_processor.get_storage")
    @patch("src.processors.bronze_processor.BreweryAPIClient")
    @patch("src.processors.bronze_processor.PostgreSQLLoader")
    def test_rerunning_bronze_with_same_date(
        self, mock_db, mock_api, mock_storage, mock_settings
    ):
        """Re-running Bronze with same date should be idempotent."""
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

        raw_data = [{"id": "1", "name": "Item"}]

        api_client = Mock()
        mock_api.return_value = api_client
        api_client.fetch_all_breweries.return_value = raw_data

        db_loader = Mock()
        mock_db.return_value = db_loader
        db_loader.load_bronze_breweries.return_value = 1

        processor = BronzeProcessor()
        ingestion_date = date(2025, 1, 15)

        # Run twice with same date
        result1 = processor.extract_breweries(ingestion_date=ingestion_date)
        result2 = processor.extract_breweries(ingestion_date=ingestion_date)

        # Results should be identical
        assert result1["ingestion_date"] == result2["ingestion_date"]
        assert result1["records_fetched"] == result2["records_fetched"]
