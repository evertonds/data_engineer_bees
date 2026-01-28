"""
Brewery API Client
Fetches data from the Open Brewery DB API with retry logic and rate limiting.
"""

import logging
import time
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class BreweryAPIClient:
    """Client for the Open Brewery DB API."""

    def __init__(
        self,
        base_url: str = "https://api.openbrewerydb.org/v1",
        rate_limit: int = 50,
        timeout: int = 30,
        max_retries: int = 3,
    ):
        """
        Initialize the Brewery API Client.

        Args:
            base_url: Base URL for the API
            rate_limit: Maximum requests per minute
            timeout: Request timeout in seconds
            max_retries: Maximum number of retries for failed requests
        """
        self.base_url = base_url
        self.rate_limit = rate_limit
        self.timeout = timeout
        self.max_retries = max_retries

        # Request tracking for rate limiting
        self._request_times: List[float] = []

        # Configure session with retry strategy
        self.session = self._create_session()

        logger.info(f"Initialized BreweryAPIClient with base_url={base_url}")

    def _create_session(self) -> requests.Session:
        """
        Create a requests session with retry strategy.

        Returns:
            Configured requests session
        """
        session = requests.Session()

        # Configure retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=1,  # Exponential backoff: 1, 2, 4 seconds
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def _rate_limit(self) -> None:
        """Implement rate limiting to avoid overwhelming the API."""
        now = time.time()

        # Remove requests older than 1 minute
        self._request_times = [t for t in self._request_times if now - t < 60]

        # Check if we've hit the rate limit
        if len(self._request_times) >= self.rate_limit:
            # Calculate sleep time
            oldest_request = self._request_times[0]
            sleep_time = 60 - (now - oldest_request)
            if sleep_time > 0:
                logger.warning(
                    f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds"
                )
                time.sleep(sleep_time)

        # Record this request
        self._request_times.append(time.time())

    def _make_request(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> Dict:
        """
        Make a request to the API with error handling.

        Args:
            endpoint: API endpoint
            params: Query parameters

        Returns:
            JSON response from API

        Raises:
            requests.exceptions.RequestException: If request fails after retries
        """
        self._rate_limit()

        # Ensure base_url ends with / for proper urljoin behavior
        base = self.base_url if self.base_url.endswith('/') else f"{self.base_url}/"
        url = urljoin(base, endpoint)

        try:
            logger.debug(f"Making request to {url} with params={params}")
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error occurred: {e}")
            raise
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection error occurred: {e}")
            raise
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout error occurred: {e}")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error occurred: {e}")
            raise

    def fetch_breweries(
        self, page: int = 1, per_page: int = 50
    ) -> List[Dict]:
        """
        Fetch a page of breweries from the API.

        Args:
            page: Page number (1-indexed)
            per_page: Number of results per page (max 200)

        Returns:
            List of brewery dictionaries
        """
        params = {"page": page, "per_page": min(per_page, 200)}

        logger.info(f"Fetching breweries page {page} (per_page={per_page})")

        data = self._make_request("breweries", params=params)

        if isinstance(data, list):
            logger.info(f"Successfully fetched {len(data)} breweries")
            return data
        else:
            logger.warning(f"Unexpected response format: {type(data)}")
            return []

    def fetch_all_breweries(
        self, per_page: int = 50, max_pages: Optional[int] = None
    ) -> List[Dict]:
        """
        Fetch all breweries from the API with pagination.

        Args:
            per_page: Number of results per page
            max_pages: Maximum number of pages to fetch (None for all)

        Returns:
            List of all brewery dictionaries
        """
        all_breweries = []
        page = 1

        logger.info("Starting to fetch all breweries")

        while True:
            if max_pages and page > max_pages:
                logger.info(f"Reached max_pages limit: {max_pages}")
                break

            try:
                breweries = self.fetch_breweries(page=page, per_page=per_page)

                if not breweries:
                    logger.info(f"No more breweries found at page {page}")
                    break

                all_breweries.extend(breweries)
                logger.info(f"Total breweries fetched so far: {len(all_breweries)}")

                page += 1

            except Exception as e:
                logger.error(f"Error fetching page {page}: {e}")
                break

        logger.info(f"Finished fetching. Total breweries: {len(all_breweries)}")
        return all_breweries

    def fetch_brewery_by_id(self, brewery_id: str) -> Optional[Dict]:
        """
        Fetch a single brewery by ID.

        Args:
            brewery_id: Brewery UUID

        Returns:
            Brewery dictionary or None if not found
        """
        try:
            logger.info(f"Fetching brewery with ID: {brewery_id}")
            data = self._make_request(f"breweries/{brewery_id}")
            return data
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"Brewery {brewery_id} not found")
                return None
            raise

    def get_metadata(self) -> Dict:
        """
        Get metadata about the breweries dataset.

        Returns:
            Dictionary with dataset metadata
        """
        try:
            logger.info("Fetching metadata")
            data = self._make_request("breweries/meta")
            return data
        except Exception as e:
            logger.error(f"Error fetching metadata: {e}")
            return {}

    def search_breweries(
        self,
        query: Optional[str] = None,
        by_city: Optional[str] = None,
        by_state: Optional[str] = None,
        by_type: Optional[str] = None,
        per_page: int = 50,
    ) -> List[Dict]:
        """
        Search breweries with filters.

        Args:
            query: Search query for brewery name
            by_city: Filter by city
            by_state: Filter by state
            by_type: Filter by brewery type
            per_page: Number of results per page

        Returns:
            List of matching brewery dictionaries
        """
        params = {"per_page": min(per_page, 200)}

        if query:
            params["query"] = query
        if by_city:
            params["by_city"] = by_city
        if by_state:
            params["by_state"] = by_state
        if by_type:
            params["by_type"] = by_type

        logger.info(f"Searching breweries with params: {params}")

        data = self._make_request("breweries", params=params)

        if isinstance(data, list):
            logger.info(f"Found {len(data)} matching breweries")
            return data
        else:
            return []

    def close(self) -> None:
        """Close the session."""
        self.session.close()
        logger.info("Closed BreweryAPIClient session")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
