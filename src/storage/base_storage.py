"""
Base storage interface for abstraction between local and S3 storage.
"""

from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional


class BaseStorage(ABC):
    """Abstract base class for storage implementations."""

    @abstractmethod
    def write_json(self, data: Any, layer: str, dataset: str, filename: str) -> str:
        """
        Write JSON data to storage.

        Args:
            data: Data to write (will be serialized to JSON)
            layer: Data layer (bronze, silver, gold)
            dataset: Dataset name (e.g., 'breweries')
            filename: File name

        Returns:
            Path/URI where data was written
        """
        pass

    @abstractmethod
    def read_json(self, layer: str, dataset: str, filename: str) -> Any:
        """
        Read JSON data from storage.

        Args:
            layer: Data layer (bronze, silver, gold)
            dataset: Dataset name
            filename: File name

        Returns:
            Deserialized JSON data
        """
        pass

    @abstractmethod
    def write_parquet(
        self,
        data: Any,
        layer: str,
        dataset: str,
        partition_cols: Optional[List[str]] = None,
    ) -> str:
        """
        Write data as Parquet to storage.

        Args:
            data: Data to write (DataFrame or similar)
            layer: Data layer (bronze, silver, gold)
            dataset: Dataset name
            partition_cols: Columns to partition by

        Returns:
            Path/URI where data was written
        """
        pass

    @abstractmethod
    def read_parquet(self, layer: str, dataset: str, filters: Optional[Dict] = None) -> Any:
        """
        Read Parquet data from storage.

        Args:
            layer: Data layer (bronze, silver, gold)
            dataset: Dataset name
            filters: Optional filters to apply

        Returns:
            Data (DataFrame or similar)
        """
        pass

    @abstractmethod
    def exists(self, layer: str, dataset: str, filename: Optional[str] = None) -> bool:
        """
        Check if a path exists in storage.

        Args:
            layer: Data layer
            dataset: Dataset name
            filename: Optional filename

        Returns:
            True if exists, False otherwise
        """
        pass

    @abstractmethod
    def list_files(self, layer: str, dataset: str, pattern: str = "*") -> List[str]:
        """
        List files in a directory.

        Args:
            layer: Data layer
            dataset: Dataset name
            pattern: Glob pattern for filtering

        Returns:
            List of file paths/URIs
        """
        pass

    @abstractmethod
    def delete(self, layer: str, dataset: str, filename: Optional[str] = None) -> None:
        """
        Delete file or directory.

        Args:
            layer: Data layer
            dataset: Dataset name
            filename: Optional filename (deletes directory if not provided)
        """
        pass

    def get_dated_path(self, layer: str, dataset: str, date_obj: Optional[date] = None) -> str:
        """
        Get a date-partitioned path.

        Args:
            layer: Data layer
            dataset: Dataset name
            date_obj: Date for partitioning (defaults to today)

        Returns:
            Path string with date partitioning
        """
        if date_obj is None:
            date_obj = date.today()

        date_str = date_obj.strftime("%Y-%m-%d")
        return f"{layer}/{dataset}/{date_str}"
