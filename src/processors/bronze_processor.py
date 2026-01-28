"""
Bronze layer processor.
Extracts raw data from the Open Brewery DB API and persists it.
"""

import logging
from datetime import date
from typing import Dict, List

from src.api.brewery_client import BreweryAPIClient
from src.config.settings import get_settings
from src.storage.postgres_loader import PostgreSQLLoader
from src.storage.storage_factory import get_storage

logger = logging.getLogger(__name__)


class BronzeProcessor:
    """Processor for Bronze layer (raw data extraction)."""

    def __init__(self):
        """Initialize Bronze processor."""
        self.settings = get_settings()
        self.storage = get_storage()
        self.api_client = BreweryAPIClient(
            base_url=self.settings.api.base_url,
            rate_limit=self.settings.api.rate_limit,
            timeout=self.settings.api.timeout,
        )
        self.db_loader = PostgreSQLLoader()

        logger.info("Initialized BronzeProcessor")

    def extract_breweries(
        self, max_pages: int = None, ingestion_date: date = None
    ) -> Dict:
        """
        Extract all brewery data from API.

        Args:
            max_pages: Maximum number of pages to fetch (None for all)
            ingestion_date: Date for partitioning (defaults to today)

        Returns:
            Dictionary with extraction metadata
        """
        if ingestion_date is None:
            ingestion_date = date.today()

        logger.info(f"Starting Bronze extraction for date: {ingestion_date}")

        # Fetch data from API
        logger.info("Fetching breweries from API...")
        breweries = self.api_client.fetch_all_breweries(
            per_page=50, max_pages=max_pages
        )

        logger.info(f"Fetched {len(breweries)} breweries from API")

        if not breweries:
            logger.warning("No breweries fetched from API")
            return {
                "status": "success",
                "records_fetched": 0,
                "records_stored": 0,
                "records_loaded_db": 0,
                "ingestion_date": str(ingestion_date),
            }

        # Save raw JSON to storage
        filename = f"{ingestion_date}/breweries_raw.json"
        logger.info(f"Saving raw data to storage: {filename}")

        storage_path = self.storage.write_json(
            data=breweries, layer="bronze", dataset="breweries", filename=filename
        )

        logger.info(f"Raw data saved to: {storage_path}")

        # Load data into PostgreSQL bronze schema
        logger.info("Loading data into breweries_bronze.tb_breweries table...")
        rows_loaded = self.db_loader.load_bronze_breweries(breweries)

        logger.info(f"Bronze extraction complete: {rows_loaded} rows loaded to database")

        return {
            "status": "success",
            "records_fetched": len(breweries),
            "records_stored": len(breweries),
            "records_loaded_db": rows_loaded,
            "storage_path": storage_path,
            "ingestion_date": str(ingestion_date),
        }

    def get_bronze_data_for_processing(
        self, ingestion_date: date = None
    ) -> List[Dict]:
        """
        Get raw data from Bronze layer for processing.

        Args:
            ingestion_date: Date to retrieve (defaults to today)

        Returns:
            List of brewery dictionaries
        """
        if ingestion_date is None:
            ingestion_date = date.today()

        filename = f"{ingestion_date}/breweries_raw.json"
        logger.info(f"Reading Bronze data from: {filename}")

        try:
            data = self.storage.read_json(
                layer="bronze", dataset="breweries", filename=filename
            )
            logger.info(f"Read {len(data)} records from Bronze storage")
            return data
        except FileNotFoundError:
            logger.error(f"Bronze data not found for date: {ingestion_date}")
            raise

    def collect_bronze_stats(self, data: List[Dict]) -> Dict:
        """
        Collect statistics from bronze data (no validation - all data accepted).

        Bronze layer accepts ANY data from the API without validation.
        All validations and data quality checks are performed in Silver layer.

        Args:
            data: List of brewery dictionaries

        Returns:
            Statistics for observability
        """
        logger.info(f"Collecting stats from {len(data)} records...")

        records_with_coordinates = 0
        records_with_website = 0
        unique_ids = set()
        duplicate_ids = []

        for record in data:
            # Track duplicates for observability (but still insert them)
            record_id = record.get("id")
            if record_id:
                if record_id in unique_ids:
                    duplicate_ids.append(record_id)
                unique_ids.add(record_id)

            # Track optional fields
            if record.get("longitude") and record.get("latitude"):
                records_with_coordinates += 1

            if record.get("website_url"):
                records_with_website += 1

        stats = {
            "total_records": len(data),
            "unique_ids": len(unique_ids),
            "duplicate_ids_count": len(duplicate_ids),
            "records_with_coordinates": records_with_coordinates,
            "records_with_website": records_with_website,
        }

        logger.info(f"Bronze statistics: {stats}")

        return stats

    def run(self, max_pages: int = None) -> Dict:
        """
        Run the complete Bronze extraction process.

        Bronze layer accepts ALL data without validation or rejection.
        All data quality checks and validations are performed in Silver layer.

        Args:
            max_pages: Maximum number of pages to fetch (None for all)

        Returns:
            Processing results
        """
        try:
            # Extract data
            extraction_results = self.extract_breweries(max_pages=max_pages)

            # Collect statistics for observability (no validation)
            if extraction_results["records_fetched"] > 0:
                data = self.get_bronze_data_for_processing()
                stats = self.collect_bronze_stats(data)
                extraction_results["statistics"] = stats

            return extraction_results

        except Exception as e:
            logger.error(f"Bronze processing failed: {e}", exc_info=True)
            raise

    def close(self):
        """Clean up resources."""
        self.api_client.close()
        self.db_loader.close()
        logger.info("Closed BronzeProcessor resources")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
