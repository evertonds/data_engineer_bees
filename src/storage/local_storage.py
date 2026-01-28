"""
Local filesystem storage implementation.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import pyarrow.parquet as pq

from src.storage.base_storage import BaseStorage

logger = logging.getLogger(__name__)


class LocalStorage(BaseStorage):
    """Local filesystem storage implementation."""

    def __init__(self, base_path: str = "/opt/airflow/data"):
        """
        Initialize local storage.

        Args:
            base_path: Base path for data storage
        """
        self.base_path = Path(base_path)
        logger.info(f"Initialized LocalStorage with base_path={self.base_path}")

        # Ensure base path exists
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_path(self, layer: str, dataset: str, filename: Optional[str] = None) -> Path:
        """
        Get full path for a file.

        Args:
            layer: Data layer
            dataset: Dataset name
            filename: Optional filename

        Returns:
            Full Path object
        """
        path = self.base_path / layer / dataset
        if filename:
            path = path / filename
        return path

    def write_json(self, data: Any, layer: str, dataset: str, filename: str) -> str:
        """Write JSON data to local filesystem."""
        file_path = self._get_path(layer, dataset, filename)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Writing JSON to {file_path}")

        with open(file_path, "w") as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Successfully wrote JSON to {file_path}")
        return str(file_path)

    def read_json(self, layer: str, dataset: str, filename: str) -> Any:
        """Read JSON data from local filesystem."""
        file_path = self._get_path(layer, dataset, filename)

        logger.info(f"Reading JSON from {file_path}")

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, "r") as f:
            data = json.load(f)

        logger.info(f"Successfully read JSON from {file_path}")
        return data

    def write_parquet(
        self,
        data: Any,
        layer: str,
        dataset: str,
        partition_cols: Optional[List[str]] = None,
    ) -> str:
        """Write data as Parquet to local filesystem."""
        dir_path = self._get_path(layer, dataset)
        dir_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"Writing Parquet to {dir_path}")

        # Convert to pandas DataFrame if needed
        if isinstance(data, pd.DataFrame):
            df = data
        else:
            # Assume it's a PySpark DataFrame
            df = data.toPandas()

        # Write with or without partitioning
        if partition_cols:
            logger.info(f"Writing with partitioning: {partition_cols}")
            df.to_parquet(
                dir_path,
                engine="pyarrow",
                compression="snappy",
                partition_cols=partition_cols,
                index=False,
            )
        else:
            file_path = dir_path / "data.parquet"
            df.to_parquet(
                file_path,
                engine="pyarrow",
                compression="snappy",
                index=False,
            )

        logger.info(f"Successfully wrote Parquet to {dir_path}")
        return str(dir_path)

    def read_parquet(
        self, layer: str, dataset: str, filters: Optional[Dict] = None
    ) -> pd.DataFrame:
        """Read Parquet data from local filesystem."""
        dir_path = self._get_path(layer, dataset)

        logger.info(f"Reading Parquet from {dir_path}")

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {dir_path}")

        # Read parquet (handles both single files and partitioned datasets)
        try:
            df = pd.read_parquet(dir_path, engine="pyarrow", filters=filters)
            logger.info(f"Successfully read {len(df)} rows from {dir_path}")
            return df
        except Exception as e:
            logger.error(f"Error reading parquet from {dir_path}: {e}")
            raise

    def exists(self, layer: str, dataset: str, filename: Optional[str] = None) -> bool:
        """Check if a path exists in local filesystem."""
        path = self._get_path(layer, dataset, filename)
        exists = path.exists()
        logger.debug(f"Checked existence of {path}: {exists}")
        return exists

    def list_files(self, layer: str, dataset: str, pattern: str = "*") -> List[str]:
        """List files in a directory."""
        dir_path = self._get_path(layer, dataset)

        if not dir_path.exists():
            logger.warning(f"Directory does not exist: {dir_path}")
            return []

        files = [str(p.relative_to(self.base_path)) for p in dir_path.glob(pattern) if p.is_file()]
        logger.info(f"Found {len(files)} files matching pattern '{pattern}' in {dir_path}")
        return files

    def delete(self, layer: str, dataset: str, filename: Optional[str] = None) -> None:
        """Delete file or directory from local filesystem."""
        path = self._get_path(layer, dataset, filename)

        if not path.exists():
            logger.warning(f"Path does not exist: {path}")
            return

        if path.is_file():
            path.unlink()
            logger.info(f"Deleted file: {path}")
        else:
            import shutil
            shutil.rmtree(path)
            logger.info(f"Deleted directory: {path}")
