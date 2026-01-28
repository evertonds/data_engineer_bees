"""
Configuration settings for the Brewery Pipeline.
Loads configuration from environment variables.
"""

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


@dataclass
class APIConfig:
    """API configuration settings."""

    base_url: str = os.getenv("BREWERY_API_URL", "https://api.openbrewerydb.org/v1")
    rate_limit: int = int(os.getenv("BREWERY_API_RATE_LIMIT", "50"))
    timeout: int = int(os.getenv("BREWERY_API_TIMEOUT", "30"))


@dataclass
class DatabaseConfig:
    """Database configuration settings."""

    host: str = os.getenv("POSTGRES_HOST", "localhost")
    port: int = int(os.getenv("POSTGRES_PORT", "5432"))
    database: str = os.getenv("POSTGRES_DB", "breweries")
    user: str = os.getenv("POSTGRES_USER", "airflow")
    password: str = os.getenv("POSTGRES_PASSWORD", "")

    @property
    def connection_string(self) -> str:
        """Get PostgreSQL connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def sqlalchemy_uri(self) -> str:
        """Get SQLAlchemy URI."""
        return f"postgresql+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class StorageConfig:
    """Storage configuration settings."""

    storage_type: str = os.getenv("STORAGE_TYPE", "local")
    local_data_path: str = os.getenv("LOCAL_DATA_PATH", "/opt/airflow/data")

    # S3 configuration
    s3_bucket_bronze: str = os.getenv("S3_BUCKET_BRONZE", "brewery-data-lake-bronze-dev")
    s3_bucket_silver: str = os.getenv("S3_BUCKET_SILVER", "brewery-data-lake-silver-dev")
    s3_bucket_gold: str = os.getenv("S3_BUCKET_GOLD", "brewery-data-lake-gold-dev")

    @property
    def is_local(self) -> bool:
        """Check if using local storage."""
        return self.storage_type.lower() == "local"

    @property
    def is_s3(self) -> bool:
        """Check if using S3 storage."""
        return self.storage_type.lower() == "s3"


@dataclass
class AWSConfig:
    """AWS configuration settings."""

    access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    region: str = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    session_token: Optional[str] = os.getenv("AWS_SESSION_TOKEN")


@dataclass
class SparkConfig:
    """Spark configuration settings."""

    master: str = os.getenv("SPARK_MASTER", "local[*]")
    driver_memory: str = os.getenv("SPARK_DRIVER_MEMORY", "2g")
    executor_memory: str = os.getenv("SPARK_EXECUTOR_MEMORY", "2g")
    app_name: str = os.getenv("SPARK_APP_NAME", "BreweryPipeline")


@dataclass
class GreatExpectationsConfig:
    """Great Expectations configuration settings."""

    checkpoint_enabled: bool = os.getenv("GE_CHECKPOINT_ENABLED", "true").lower() == "true"
    data_docs_enabled: bool = os.getenv("GE_DATA_DOCS_ENABLED", "true").lower() == "true"


@dataclass
class DBTConfig:
    """dbt configuration settings."""

    profiles_dir: str = os.getenv("DBT_PROFILES_DIR", "/opt/airflow/dbt_project")
    target: str = os.getenv("DBT_TARGET", "dev")


@dataclass
class PipelineConfig:
    """Pipeline configuration settings."""

    schedule: str = os.getenv("PIPELINE_SCHEDULE", "0 2 * * *")
    retries: int = int(os.getenv("PIPELINE_RETRIES", "3"))
    retry_delay_seconds: int = int(os.getenv("PIPELINE_RETRY_DELAY", "300"))


@dataclass
class LoggingConfig:
    """Logging configuration settings."""

    log_level: str = os.getenv("LOG_LEVEL", "INFO")


class Settings:
    """Main settings class that aggregates all configuration."""

    def __init__(self):
        self.api = APIConfig()
        self.database = DatabaseConfig()
        self.storage = StorageConfig()
        self.aws = AWSConfig()
        self.spark = SparkConfig()
        self.great_expectations = GreatExpectationsConfig()
        self.dbt = DBTConfig()
        self.pipeline = PipelineConfig()
        self.logging = LoggingConfig()

    def validate(self) -> None:
        """Validate configuration settings."""
        errors = []

        # Validate database password
        if not self.database.password:
            errors.append("POSTGRES_PASSWORD is required")

        # Validate S3 configuration if using S3 storage
        if self.storage.is_s3:
            if not self.aws.access_key_id:
                errors.append("AWS_ACCESS_KEY_ID is required when using S3 storage")
            if not self.aws.secret_access_key:
                errors.append("AWS_SECRET_ACCESS_KEY is required when using S3 storage")

        if errors:
            raise ValueError(f"Configuration validation failed:\n" + "\n".join(f"- {e}" for e in errors))

    def __repr__(self) -> str:
        """String representation (hide sensitive data)."""
        return (
            f"Settings(\n"
            f"  api={self.api},\n"
            f"  database=DatabaseConfig(host={self.database.host}, port={self.database.port}, "
            f"database={self.database.database}, user={self.database.user}, password=***),\n"
            f"  storage={self.storage},\n"
            f"  aws=AWSConfig(region={self.aws.region}, access_key=***),\n"
            f"  spark={self.spark},\n"
            f"  great_expectations={self.great_expectations},\n"
            f"  dbt={self.dbt},\n"
            f"  pipeline={self.pipeline},\n"
            f"  logging={self.logging}\n"
            f")"
        )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
