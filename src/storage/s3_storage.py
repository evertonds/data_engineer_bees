"""
Amazon S3 storage implementation.
"""

import io
import json
import logging
from typing import Any, Dict, List, Optional

import boto3
import pandas as pd
from botocore.exceptions import ClientError

from src.storage.base_storage import BaseStorage

logger = logging.getLogger(__name__)


class S3Storage(BaseStorage):
    """Amazon S3 storage implementation."""

    def __init__(
        self,
        bucket_bronze: str,
        bucket_silver: str,
        bucket_gold: str,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1",
    ):
        """
        Initialize S3 storage.

        Args:
            bucket_bronze: S3 bucket for bronze layer
            bucket_silver: S3 bucket for silver layer
            bucket_gold: S3 bucket for gold layer
            aws_access_key_id: AWS access key ID (optional, can use IAM role)
            aws_secret_access_key: AWS secret access key (optional, can use IAM role)
            region_name: AWS region
        """
        self.buckets = {
            "bronze": bucket_bronze,
            "silver": bucket_silver,
            "gold": bucket_gold,
        }

        # Initialize S3 client
        session_kwargs = {"region_name": region_name}
        if aws_access_key_id and aws_secret_access_key:
            session_kwargs["aws_access_key_id"] = aws_access_key_id
            session_kwargs["aws_secret_access_key"] = aws_secret_access_key

        self.s3_client = boto3.client("s3", **session_kwargs)
        self.s3_resource = boto3.resource("s3", **session_kwargs)

        logger.info(f"Initialized S3Storage with buckets: {self.buckets}")

    def _get_bucket(self, layer: str) -> str:
        """Get bucket name for a layer."""
        return self.buckets.get(layer, self.buckets["bronze"])

    def _get_key(self, dataset: str, filename: Optional[str] = None) -> str:
        """Get S3 key for a file."""
        if filename:
            return f"{dataset}/{filename}"
        return f"{dataset}/"

    def _get_s3_uri(self, layer: str, dataset: str, filename: Optional[str] = None) -> str:
        """Get S3 URI."""
        bucket = self._get_bucket(layer)
        key = self._get_key(dataset, filename)
        return f"s3://{bucket}/{key}"

    def write_json(self, data: Any, layer: str, dataset: str, filename: str) -> str:
        """Write JSON data to S3."""
        bucket = self._get_bucket(layer)
        key = self._get_key(dataset, filename)

        logger.info(f"Writing JSON to s3://{bucket}/{key}")

        # Serialize to JSON
        json_data = json.dumps(data, indent=2, default=str)

        # Upload to S3
        try:
            self.s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=json_data.encode("utf-8"),
                ContentType="application/json",
            )
            logger.info(f"Successfully wrote JSON to s3://{bucket}/{key}")
            return f"s3://{bucket}/{key}"
        except ClientError as e:
            logger.error(f"Error writing JSON to S3: {e}")
            raise

    def read_json(self, layer: str, dataset: str, filename: str) -> Any:
        """Read JSON data from S3."""
        bucket = self._get_bucket(layer)
        key = self._get_key(dataset, filename)

        logger.info(f"Reading JSON from s3://{bucket}/{key}")

        try:
            response = self.s3_client.get_object(Bucket=bucket, Key=key)
            data = json.loads(response["Body"].read().decode("utf-8"))
            logger.info(f"Successfully read JSON from s3://{bucket}/{key}")
            return data
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"File not found: s3://{bucket}/{key}")
            logger.error(f"Error reading JSON from S3: {e}")
            raise

    def write_parquet(
        self,
        data: Any,
        layer: str,
        dataset: str,
        partition_cols: Optional[List[str]] = None,
    ) -> str:
        """Write data as Parquet to S3."""
        bucket = self._get_bucket(layer)
        base_key = f"{dataset}/"

        logger.info(f"Writing Parquet to s3://{bucket}/{base_key}")

        # Convert to pandas DataFrame if needed
        if isinstance(data, pd.DataFrame):
            df = data
        else:
            # Assume it's a PySpark DataFrame
            df = data.toPandas()

        # Write to S3
        s3_path = f"s3://{bucket}/{base_key}"

        try:
            if partition_cols:
                logger.info(f"Writing with partitioning: {partition_cols}")
                df.to_parquet(
                    s3_path,
                    engine="pyarrow",
                    compression="snappy",
                    partition_cols=partition_cols,
                    index=False,
                )
            else:
                df.to_parquet(
                    f"{s3_path}data.parquet",
                    engine="pyarrow",
                    compression="snappy",
                    index=False,
                )

            logger.info(f"Successfully wrote Parquet to {s3_path}")
            return s3_path
        except Exception as e:
            logger.error(f"Error writing Parquet to S3: {e}")
            raise

    def read_parquet(
        self, layer: str, dataset: str, filters: Optional[Dict] = None
    ) -> pd.DataFrame:
        """Read Parquet data from S3."""
        bucket = self._get_bucket(layer)
        base_key = f"{dataset}/"
        s3_path = f"s3://{bucket}/{base_key}"

        logger.info(f"Reading Parquet from {s3_path}")

        try:
            df = pd.read_parquet(s3_path, engine="pyarrow", filters=filters)
            logger.info(f"Successfully read {len(df)} rows from {s3_path}")
            return df
        except Exception as e:
            logger.error(f"Error reading Parquet from S3: {e}")
            raise

    def exists(self, layer: str, dataset: str, filename: Optional[str] = None) -> bool:
        """Check if a path exists in S3."""
        bucket = self._get_bucket(layer)
        key = self._get_key(dataset, filename)

        try:
            if filename:
                # Check for specific file
                self.s3_client.head_object(Bucket=bucket, Key=key)
                logger.debug(f"File exists: s3://{bucket}/{key}")
                return True
            else:
                # Check for prefix
                response = self.s3_client.list_objects_v2(
                    Bucket=bucket, Prefix=key, MaxKeys=1
                )
                exists = "Contents" in response
                logger.debug(f"Prefix exists: s3://{bucket}/{key}: {exists}")
                return exists
        except ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            logger.error(f"Error checking existence in S3: {e}")
            raise

    def list_files(self, layer: str, dataset: str, pattern: str = "*") -> List[str]:
        """List files in an S3 prefix."""
        bucket = self._get_bucket(layer)
        prefix = f"{dataset}/"

        logger.info(f"Listing files in s3://{bucket}/{prefix}")

        try:
            paginator = self.s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=bucket, Prefix=prefix)

            files = []
            for page in pages:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        key = obj["Key"]
                        # Simple pattern matching (only supports * wildcard)
                        if pattern == "*" or key.endswith(pattern.replace("*", "")):
                            files.append(f"s3://{bucket}/{key}")

            logger.info(f"Found {len(files)} files in s3://{bucket}/{prefix}")
            return files
        except ClientError as e:
            logger.error(f"Error listing files in S3: {e}")
            raise

    def delete(self, layer: str, dataset: str, filename: Optional[str] = None) -> None:
        """Delete file or prefix from S3."""
        bucket = self._get_bucket(layer)
        key = self._get_key(dataset, filename)

        logger.info(f"Deleting from s3://{bucket}/{key}")

        try:
            if filename:
                # Delete single file
                self.s3_client.delete_object(Bucket=bucket, Key=key)
                logger.info(f"Deleted file: s3://{bucket}/{key}")
            else:
                # Delete all objects with prefix
                paginator = self.s3_client.get_paginator("list_objects_v2")
                pages = paginator.paginate(Bucket=bucket, Prefix=key)

                delete_count = 0
                for page in pages:
                    if "Contents" in page:
                        objects = [{"Key": obj["Key"]} for obj in page["Contents"]]
                        self.s3_client.delete_objects(
                            Bucket=bucket, Delete={"Objects": objects}
                        )
                        delete_count += len(objects)

                logger.info(f"Deleted {delete_count} objects from s3://{bucket}/{key}")
        except ClientError as e:
            logger.error(f"Error deleting from S3: {e}")
            raise
