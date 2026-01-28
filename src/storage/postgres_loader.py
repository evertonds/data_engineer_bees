"""
PostgreSQL loader for loading data into database tables.
"""

import logging
from datetime import datetime
from typing import Dict, List

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.config.settings import get_settings

logger = logging.getLogger(__name__)


class PostgreSQLLoader:
    """Loader for PostgreSQL database."""

    def __init__(self, connection_string: str = None):
        """
        Initialize PostgreSQL loader.

        Args:
            connection_string: PostgreSQL connection string (optional, uses settings if not provided)
        """
        if connection_string is None:
            settings = get_settings()
            connection_string = settings.database.sqlalchemy_uri

        self.connection_string = connection_string
        self.engine: Engine = create_engine(connection_string)
        logger.info("Initialized PostgreSQLLoader")

    def load_bronze_breweries(self, data: List[Dict]) -> int:
        """
        Load brewery data into breweries_bronze.tb_breweries table.

        Args:
            data: List of brewery dictionaries from API

        Returns:
            Number of rows inserted

        """
        if not data:
            logger.warning("No data to load")
            return 0

        logger.info(f"Loading {len(data)} records into breweries_bronze.tb_breweries")

        # Convert to DataFrame
        df = pd.DataFrame(data)

        # Add metadata columns
        df["ingestion_timestamp"] = datetime.now()
        df["ingestion_date"] = datetime.now().date()

        # Ensure all expected columns exist
        expected_cols = [
            "id",
            "name",
            "brewery_type",
            "address_1",
            "address_2",
            "address_3",
            "city",
            "state_province",
            "postal_code",
            "country",
            "longitude",
            "latitude",
            "phone",
            "website_url",
            "state",
            "street",
            "ingestion_timestamp",
            "ingestion_date",
        ]

        for col in expected_cols:
            if col not in df.columns:
                df[col] = None

        # Select only expected columns in correct order
        df = df[expected_cols]

        # Load to database (replace existing data for idempotency)
        try:
            df.to_sql(
                "tb_breweries",
                self.engine,
                schema="breweries_bronze",
                if_exists="append",
                index=False,
                method="multi",
            )
            logger.info(f"Successfully loaded {len(df)} records into breweries_bronze.tb_breweries")
            return len(df)
        except Exception as e:
            logger.error(f"Error loading data into breweries_bronze.tb_breweries: {e}")
            raise

    def load_silver_breweries(self, df: pd.DataFrame) -> int:
        """
        Load cleaned brewery data into breweries_silver.tb_breweries table.

        Args:
            df: DataFrame with cleaned brewery data

        Returns:
            Number of rows inserted
        """
        if df.empty:
            logger.warning("No data to load")
            return 0

        logger.info(f"Loading {len(df)} records into breweries_silver.tb_breweries")

        # Truncate and load (replace strategy for silver layer)
        try:
            with self.engine.begin() as conn:
                conn.execute(text("TRUNCATE TABLE breweries_silver.tb_breweries"))

            df.to_sql(
                "tb_breweries",
                self.engine,
                schema="breweries_silver",
                if_exists="append",
                index=False,
                method="multi",
            )
            logger.info(f"Successfully loaded {len(df)} records into breweries_silver.tb_breweries")
            return len(df)
        except Exception as e:
            logger.error(f"Error loading data into breweries_silver.tb_breweries: {e}")
            raise

    def load_gold_aggregates(self, df: pd.DataFrame) -> int:
        """
        Load aggregated data into breweries_gold.fat_breweries_by_type_location table.

        Args:
            df: DataFrame with aggregated brewery counts

        Returns:
            Number of rows inserted
        """
        if df.empty:
            logger.warning("No data to load")
            return 0

        logger.info(f"Loading {len(df)} records into breweries_gold.fat_breweries_by_type_location")

        # Add last_updated timestamp
        df["last_updated"] = datetime.now()

        # Truncate and load (replace strategy for gold layer)
        try:
            with self.engine.connect() as conn:
                conn.execute(text("TRUNCATE TABLE breweries_gold.fat_breweries_by_type_location"))
                conn.commit()

            df.to_sql(
                "fat_breweries_by_type_location",
                self.engine,
                schema="breweries_gold",
                if_exists="append",
                index=False,
                method="multi",
            )
            logger.info(
                f"Successfully loaded {len(df)} records into breweries_gold.fat_breweries_by_type_location"
            )
            return len(df)
        except Exception as e:
            logger.error(f"Error loading data into breweries_gold.fat_breweries_by_type_location: {e}")
            raise

    def get_row_count(self, schema: str, table: str) -> int:
        """
        Get row count for a table.

        Args:
            schema: Schema name
            table: Table name

        Returns:
            Number of rows in table
        """
        query = f"SELECT COUNT(*) as count FROM {schema}.{table}"

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text(query))
                count = result.fetchone()[0]
                logger.info(f"Row count for {schema}.{table}: {count}")
                return count
        except Exception as e:
            logger.error(f"Error getting row count: {e}")
            raise

    def execute_query(self, query: str) -> pd.DataFrame:
        """
        Execute a SQL query and return results as DataFrame.

        Args:
            query: SQL query string

        Returns:
            Query results as DataFrame
        """
        logger.info(f"Executing query: {query[:100]}...")

        try:
            df = pd.read_sql_query(query, self.engine)
            logger.info(f"Query returned {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise

    def close(self):
        """Close database connection."""
        self.engine.dispose()
        logger.info("Closed PostgreSQL connection")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
