"""
Silver layer processor.
Cleans and transforms Bronze data using PySpark.
"""

import logging
from datetime import date
from typing import Dict

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    BooleanType,
    DateType,
    DecimalType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from src.config.settings import get_settings
from src.storage.postgres_loader import PostgreSQLLoader
from src.storage.storage_factory import get_storage

logger = logging.getLogger(__name__)


class SilverProcessor:
    """Processor for Silver layer (cleaned and transformed data)."""

    # Valid brewery types from API documentation
    VALID_BREWERY_TYPES = {
        "micro",
        "nano",
        "regional",
        "brewpub",
        "large",
        "planning",
        "bar",
        "contract",
        "proprietor",
        "closed",
        "taproom",
        "beergarden",
        "cidery",
        "location",
    }

    def __init__(self):
        """Initialize Silver processor."""
        self.settings = get_settings()
        self.storage = get_storage()
        self.db_loader = PostgreSQLLoader()

        # Initialize Spark session
        self.spark = self._create_spark_session()

        logger.info("Initialized SilverProcessor")

    def _create_spark_session(self) -> SparkSession:
        """
        Create and configure Spark session.

        Returns:
            Configured SparkSession
        """
        logger.info("Creating Spark session...")

        spark = (
            SparkSession.builder.appName(self.settings.spark.app_name)
            .master(self.settings.spark.master)
            .config("spark.driver.memory", self.settings.spark.driver_memory)
            .config("spark.executor.memory", self.settings.spark.executor_memory)
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
            .config("spark.jars", "/opt/airflow/jars/postgresql-42.6.0.jar")
            .config("spark.driver.extraClassPath", "/opt/airflow/jars/postgresql-42.6.0.jar")
            .config("spark.executor.extraClassPath", "/opt/airflow/jars/postgresql-42.6.0.jar")
            .getOrCreate()
        )

        logger.info(f"Spark session created: {spark.sparkContext.appName}")
        return spark

    def load_bronze_data(self, source_date: date = None) -> DataFrame:
        """
        Load Bronze data from PostgreSQL.

        Args:
            source_date: Date to load (defaults to today)

        Returns:
            Spark DataFrame with bronze data
        """
        if source_date is None:
            source_date = date.today()

        logger.info(f"Loading Bronze data for date: {source_date}")

        # Build connection properties
        # Build clean JDBC URL without username/password in the string
        jdbc_url = f"jdbc:postgresql://{self.settings.database.host}:{self.settings.database.port}/{self.settings.database.database}"

        # Load from breweries_bronze.tb_breweries
        df = (
            self.spark.read.format("jdbc")
            .option("url", jdbc_url)
            .option("dbtable", "breweries_bronze.tb_breweries")
            .option("user", self.settings.database.user)
            .option("password", self.settings.database.password)
            .option("driver", "org.postgresql.Driver")
            .load()
        )

        # Filter by ingestion date
        df = df.filter(F.col("ingestion_date") == source_date)

        logger.info(f"Loaded {df.count()} records from Bronze")
        return df

    def transform_data(self, df: DataFrame) -> DataFrame:
        """
        Apply transformations to Bronze data.

        Bronze layer accepts ANY data (all fields are TEXT).
        Silver layer validates, converts types, and enforces size limits.

        Args:
            df: Input DataFrame from Bronze layer

        Returns:
            Transformed DataFrame for Silver layer
        """
        logger.info("Starting Silver transformations...")
        initial_count = df.count()

        # 0. Type conversions and validations from TEXT to proper types
        logger.info("Converting types from TEXT to proper types...")

        # Convert ID from TEXT to UUID format (validate UUID format)
        df = df.withColumn(
            "id",
            F.when(
                F.col("id").rlike("^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"),
                F.col("id")
            ).otherwise(None)
        )

        # Convert longitude from TEXT to DECIMAL
        df = df.withColumn(
            "longitude",
            F.when(
                F.col("longitude").cast("decimal(11,8)").isNotNull(),
                F.col("longitude").cast("decimal(11,8)")
            ).otherwise(None)
        )

        # Convert latitude from TEXT to DECIMAL
        df = df.withColumn(
            "latitude",
            F.when(
                F.col("latitude").cast("decimal(10,8)").isNotNull(),
                F.col("latitude").cast("decimal(10,8)")
            ).otherwise(None)
        )

        # Truncate fields to match Silver schema size limits
        df = df.withColumn("name", F.substring(F.col("name"), 1, 255))
        df = df.withColumn("brewery_type", F.substring(F.col("brewery_type"), 1, 50))
        df = df.withColumn("city", F.substring(F.col("city"), 1, 100))
        df = df.withColumn("state", F.substring(F.col("state"), 1, 100))
        df = df.withColumn("state_province", F.substring(F.col("state_province"), 1, 100))
        df = df.withColumn("country", F.substring(F.col("country"), 1, 100))
        df = df.withColumn("postal_code", F.substring(F.col("postal_code"), 1, 20))
        df = df.withColumn("phone", F.substring(F.col("phone"), 1, 50))
        df = df.withColumn("address_1", F.substring(F.col("address_1"), 1, 255))
        df = df.withColumn("address_2", F.substring(F.col("address_2"), 1, 255))
        df = df.withColumn("address_3", F.substring(F.col("address_3"), 1, 255))
        df = df.withColumn("street", F.substring(F.col("street"), 1, 255))

        logger.info(f"Type conversions complete")

        # 1. Remove duplicates by ID
        df = df.dropDuplicates(["id"])
        logger.info(f"After deduplication: {df.count()} records")

        # 2. Handle nulls and create address_full
        df = df.withColumn(
            "address_full",
            F.concat_ws(
                ", ",
                F.coalesce(F.col("address_1"), F.lit("")),
                F.coalesce(F.col("address_2"), F.lit("")),
                F.coalesce(F.col("address_3"), F.lit("")),
            ),
        )

        # Clean empty address_full
        df = df.withColumn(
            "address_full",
            F.when(F.trim(F.col("address_full")) == "", None).otherwise(
                F.col("address_full")
            ),
        )

        # 3. Standardize state names (use state_province if state is null)
        df = df.withColumn(
            "state", F.coalesce(F.col("state"), F.col("state_province"))
        )

        # 4. Clean phone numbers (remove special characters)
        df = df.withColumn(
            "phone", F.regexp_replace(F.col("phone"), "[^0-9]", "")
        )

        # 5. Validate and clean URLs
        df = df.withColumn(
            "website_url",
            F.when(
                F.col("website_url").rlike("^https?://"), F.col("website_url")
            ).otherwise(None),
        )

        # 6. Create feature flags
        df = df.withColumn(
            "has_coordinates",
            (F.col("longitude").isNotNull()) & (F.col("latitude").isNotNull()),
        )

        df = df.withColumn("has_website", F.col("website_url").isNotNull())

        # 7. Validate coordinates
        df = df.withColumn(
            "latitude",
            F.when(
                (F.col("latitude") >= -90) & (F.col("latitude") <= 90),
                F.col("latitude"),
            ).otherwise(None),
        )

        df = df.withColumn(
            "longitude",
            F.when(
                (F.col("longitude") >= -180) & (F.col("longitude") <= 180),
                F.col("longitude"),
            ).otherwise(None),
        )

        # 8. Validate brewery_type
        valid_types = list(self.VALID_BREWERY_TYPES)
        df = df.withColumn(
            "brewery_type",
            F.when(
                F.col("brewery_type").isin(valid_types), F.col("brewery_type")
            ).otherwise("unknown"),
        )

        # 9. Calculate data quality score (0-1)
        df = df.withColumn(
            "data_quality_score",
            (
                # Required fields (weight: 0.4)
                F.when(F.col("id").isNotNull(), 0.1).otherwise(0)
                + F.when(F.col("name").isNotNull(), 0.1).otherwise(0)
                + F.when(F.col("city").isNotNull(), 0.1).otherwise(0)
                + F.when(F.col("state").isNotNull(), 0.1).otherwise(0)
                # Optional important fields (weight: 0.6)
                + F.when(F.col("has_coordinates"), 0.2).otherwise(0)
                + F.when(F.col("has_website"), 0.2).otherwise(0)
                + F.when(F.col("phone").isNotNull(), 0.1).otherwise(0)
                + F.when(F.col("postal_code").isNotNull(), 0.1).otherwise(0)
            ),
        )

        # 10. Add metadata
        df = df.withColumn("processed_timestamp", F.current_timestamp())
        df = df.withColumn("source_date", F.col("ingestion_date"))

        # 11. Create partition columns (trim, lowercase, and replace spaces with underscores)
        df = df.withColumn("partition_country",
                          F.lower(F.regexp_replace(F.trim(F.col("country")), "\\s+", "_")))
        df = df.withColumn("partition_state",
                          F.lower(F.regexp_replace(F.trim(F.col("state")), "\\s+", "_")))
        df = df.withColumn("partition_city",
                          F.lower(F.regexp_replace(F.trim(F.col("city")), "\\s+", "_")))

        # 12. Filter out records without required fields
        df = df.filter(
            F.col("id").isNotNull()
            & F.col("name").isNotNull()
            & F.col("brewery_type").isNotNull()
            & F.col("city").isNotNull()
            & F.col("state").isNotNull()
            & F.col("country").isNotNull()
        )

        final_count = df.count()
        rejected_count = initial_count - final_count
        logger.info(f"After transformations: {final_count} records")
        logger.info(f"Rejected records (invalid or missing required fields): {rejected_count}")

        if rejected_count > 0:
            rejection_rate = (rejected_count / initial_count * 100) if initial_count > 0 else 0
            logger.warning(f"Rejection rate: {rejection_rate:.2f}% ({rejected_count}/{initial_count})")

        # 13. Select and order columns for Silver schema
        silver_df = df.select(
            "id",
            "name",
            "brewery_type",
            "address_full",
            "city",
            "state",
            "postal_code",
            "country",
            "longitude",
            "latitude",
            "has_coordinates",
            "phone",
            "website_url",
            "has_website",
            "processed_timestamp",
            "source_date",
            "data_quality_score",
            "partition_country",
            "partition_state",
            "partition_city",
        )

        logger.info("Silver transformations complete")
        return silver_df

    def save_to_storage(self, df: DataFrame) -> str:
        """
        Save Silver data to storage (Parquet format with partitioning).

        Args:
            df: Silver DataFrame

        Returns:
            Storage path
        """
        logger.info("Saving Silver data to storage...")

        # Convert to Pandas for storage abstraction
        pandas_df = df.toPandas()

        storage_path = self.storage.write_parquet(
            data=pandas_df,
            layer="silver",
            dataset="breweries",
            partition_cols=["partition_country", "partition_state"],
        )

        logger.info(f"Silver data saved to: {storage_path}")
        return storage_path

    def save_to_database(self, df: DataFrame) -> int:
        """
        Save Silver data to PostgreSQL.

        Args:
            df: Silver DataFrame

        Returns:
            Number of rows loaded
        """
        logger.info("Saving Silver data to database...")

        # Convert to Pandas
        pandas_df = df.toPandas()

        # Load to database
        rows_loaded = self.db_loader.load_silver_breweries(pandas_df)

        logger.info(f"Loaded {rows_loaded} records to breweries_silver.tb_breweries")
        return rows_loaded

    def run(self, source_date: date = None) -> Dict:
        """
        Run the complete Silver processing pipeline.

        Args:
            source_date: Date to process (defaults to today)

        Returns:
            Processing results
        """
        try:
            if source_date is None:
                source_date = date.today()

            logger.info(f"Starting Silver processing for date: {source_date}")

            # Load Bronze data
            bronze_df = self.load_bronze_data(source_date)
            bronze_count = bronze_df.count()

            # Transform data
            silver_df = self.transform_data(bronze_df)
            silver_count = silver_df.count()

            # Save to storage (Parquet)
            storage_path = self.save_to_storage(silver_df)

            # Save to database
            rows_loaded = self.save_to_database(silver_df)

            # Calculate statistics
            avg_quality = silver_df.agg(
                F.avg("data_quality_score")
            ).first()[0]

            results = {
                "status": "success",
                "source_date": str(source_date),
                "records_input": bronze_count,
                "records_output": silver_count,
                "records_filtered": bronze_count - silver_count,
                "records_loaded_db": rows_loaded,
                "storage_path": storage_path,
                "avg_data_quality_score": round(float(avg_quality), 3) if avg_quality else None,
            }

            logger.info(f"Silver processing complete: {results}")
            return results

        except Exception as e:
            logger.error(f"Silver processing failed: {e}", exc_info=True)
            raise

    def close(self):
        """Clean up resources."""
        self.spark.stop()
        self.db_loader.close()
        logger.info("Closed SilverProcessor resources")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
