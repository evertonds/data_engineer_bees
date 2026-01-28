"""
Storage factory for creating storage instances based on configuration.
"""

import logging

from src.config.settings import get_settings
from src.storage.base_storage import BaseStorage
from src.storage.local_storage import LocalStorage
from src.storage.s3_storage import S3Storage

logger = logging.getLogger(__name__)


def get_storage() -> BaseStorage:
    """
    Get storage instance based on configuration.

    Returns:
        Storage instance (LocalStorage or S3Storage)

    Raises:
        ValueError: If storage type is not supported
    """
    settings = get_settings()

    if settings.storage.is_local:
        logger.info("Creating LocalStorage instance")
        return LocalStorage(base_path=settings.storage.local_data_path)

    elif settings.storage.is_s3:
        logger.info("Creating S3Storage instance")
        return S3Storage(
            bucket_bronze=settings.storage.s3_bucket_bronze,
            bucket_silver=settings.storage.s3_bucket_silver,
            bucket_gold=settings.storage.s3_bucket_gold,
            aws_access_key_id=settings.aws.access_key_id,
            aws_secret_access_key=settings.aws.secret_access_key,
            region_name=settings.aws.region,
        )

    else:
        raise ValueError(f"Unsupported storage type: {settings.storage.storage_type}")
