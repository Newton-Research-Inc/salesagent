"""
Yahoo DSP API Client

HTTP client for Yahoo DSP API with retry logic, rate limiting, and error handling.
Reference: https://help.yahooinc.com/dsp-api/docs/about-the-traffic-api
"""

import logging
import time
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.adapters.yahoo_dsp.auth import YahooDSPAuthError, YahooDSPAuthManager

logger = logging.getLogger(__name__)


class YahooDSPAPIError(Exception):
    """Base exception for Yahoo DSP API errors."""

    def __init__(self, message: str, status_code: int | None = None, response_data: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class YahooDSPRateLimitError(YahooDSPAPIError):
    """Raised when API rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int | None = None):
        super().__init__(message, status_code=429)
        self.retry_after = retry_after


class YahooDSPNotFoundError(YahooDSPAPIError):
    """Raised when requested resource is not found."""

    def __init__(self, message: str):
        super().__init__(message, status_code=404)


class YahooDSPValidationError(YahooDSPAPIError):
    """Raised when request validation fails."""

    def __init__(self, message: str, errors: list[dict] | None = None):
        super().__init__(message, status_code=400)
        self.errors = errors or []


class YahooDSPClient:
    """HTTP client for Yahoo DSP API.

    Features:
    - Automatic OAuth token management (JWT-based)
    - Retry logic with exponential backoff
    - Rate limit handling
    - Request/response logging
    - Error translation to typed exceptions

    Yahoo DSP API Structure:
    - Traffic API: https://dspapi.admanagerplus.yahoo.com/traffic/
    - Reporting API: https://dspapi.admanagerplus.yahoo.com/reporting/
    
    Note: Yahoo DSP uses X-Auth-Method and X-Auth-Token headers (not Bearer token).
    """

    # Correct API base URLs for Yahoo DSP
    DEFAULT_API_BASE_URL = "https://dspapi.admanagerplus.yahoo.com"
    
    # Rate limiting configuration
    MAX_REQUESTS_PER_SECOND = 10
    RATE_LIMIT_WINDOW_SECONDS = 1.0

    def __init__(
        self,
        auth_manager: YahooDSPAuthManager,
        seat_id: str,
        api_base_url: str | None = None,
        dry_run: bool = False,
    ):
        """Initialize Yahoo DSP API client.

        Args:
            auth_manager: Authentication manager for OAuth tokens
            seat_id: Yahoo DSP seat (account) ID
            api_base_url: Base URL for API (uses default if not specified)
            dry_run: If True, log requests but don't execute them
        """
        self.auth_manager = auth_manager
        self.seat_id = seat_id
        self.api_base_url = (api_base_url or self.DEFAULT_API_BASE_URL).rstrip("/")
        self.dry_run = dry_run

        # Create session with retry logic
        self._session = self._create_session()

        # Rate limiting state
        self._request_timestamps: list[float] = []

    def _create_session(self) -> requests.Session:
        """Create configured requests session with retries."""
        session = requests.Session()

        # Configure retry strategy
        # NOTE: Removed 500 from retry list to see actual error response for debugging
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[502, 503, 504],  # Don't retry 500 - we want to see the error
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)

        return session

    def _wait_for_rate_limit(self) -> None:
        """Implement simple rate limiting."""
        current_time = time.time()

        # Remove timestamps outside the window
        self._request_timestamps = [
            ts for ts in self._request_timestamps
            if current_time - ts < self.RATE_LIMIT_WINDOW_SECONDS
        ]

        # If at limit, wait
        if len(self._request_timestamps) >= self.MAX_REQUESTS_PER_SECOND:
            oldest_in_window = min(self._request_timestamps)
            wait_time = self.RATE_LIMIT_WINDOW_SECONDS - (current_time - oldest_in_window)
            if wait_time > 0:
                logger.debug(f"Rate limiting: waiting {wait_time:.2f}s")
                time.sleep(wait_time)

        self._request_timestamps.append(time.time())

    def _get_headers(self) -> dict[str, str]:
        """Get request headers including auth token.
        
        Yahoo DSP uses:
        - X-Auth-Method: OAuth2
        - X-Auth-Token: <access_token>
        - Content-Type: application/json
        """
        headers = self.auth_manager.get_auth_headers()
        headers["Content-Type"] = "application/json"
        return headers

    def _handle_response(self, response: requests.Response) -> dict[str, Any]:
        """Handle API response, raising appropriate exceptions for errors.

        Yahoo DSP returns responses in format:
        {
            "response": [...data...],  # The actual data
            "errors": null,            # Error array if any
            "timeStamp": "..."         # Timestamp
        }

        Args:
            response: HTTP response object

        Returns:
            Parsed JSON response data

        Raises:
            YahooDSPAuthError: For 401 responses
            YahooDSPRateLimitError: For 429 responses
            YahooDSPNotFoundError: For 404 responses
            YahooDSPValidationError: For 400 responses
            YahooDSPAPIError: For other error responses
        """
        # Try to parse JSON response
        try:
            data = response.json() if response.content else {}
        except ValueError:
            data = {"raw_response": response.text}

        # Handle success
        if response.ok:
            return data

        # Handle specific error codes
        status_code = response.status_code
        
        # Yahoo DSP error format can vary
        error_message = (
            data.get("response_message") or
            data.get("error_message") or
            data.get("message") or
            data.get("error") or
            data.get("detail") or
            f"HTTP {status_code}"
        )

        if status_code == 401:
            # Invalidate token and raise auth error
            self.auth_manager.invalidate_token()
            raise YahooDSPAuthError(f"Authentication failed: {error_message}")

        elif status_code == 429:
            retry_after = response.headers.get("Retry-After")
            retry_seconds = int(retry_after) if retry_after else 60
            raise YahooDSPRateLimitError(
                f"Rate limit exceeded. Retry after {retry_seconds}s",
                retry_after=retry_seconds
            )

        elif status_code == 404:
            raise YahooDSPNotFoundError(f"Resource not found: {error_message}")

        elif status_code in (400, 422):
            # Log full response for debugging
            logger.error(f"Yahoo DSP validation error ({status_code}): {data}")
            errors = data.get("errors", [])
            # Include full response in error message for debugging
            full_message = f"Validation error: {error_message}"
            if data and data != {"raw_response": ""}:
                full_message += f" | Response: {data}"
            raise YahooDSPValidationError(full_message, errors=errors)

        else:
            # Log full response for debugging
            logger.error(f"Yahoo DSP API error ({status_code}): {data}")
            raise YahooDSPAPIError(
                f"API error ({status_code}): {error_message} | Response: {data}",
                status_code=status_code,
                response_data=data
            )

    def get(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make GET request to Yahoo DSP API.

        Args:
            endpoint: API endpoint path (e.g., "traffic/campaigns")
            params: Query parameters

        Returns:
            Parsed JSON response

        Raises:
            YahooDSPAPIError: For API errors
        """
        # Ensure endpoint starts with /
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
            
        url = f"{self.api_base_url}{endpoint}"

        if self.dry_run:
            logger.info(f"[DRY RUN] GET {url} params={params}")
            return {"dry_run": True, "method": "GET", "url": url, "params": params}

        self._wait_for_rate_limit()

        logger.debug(f"GET {url} params={params}")
        response = self._session.get(
            url,
            params=params,
            headers=self._get_headers(),
            timeout=60,
        )

        return self._handle_response(response)

    def post(
        self,
        endpoint: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Make POST request to Yahoo DSP API.

        Args:
            endpoint: API endpoint path
            data: Request body data

        Returns:
            Parsed JSON response

        Raises:
            YahooDSPAPIError: For API errors
        """
        # Ensure endpoint starts with /
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
            
        url = f"{self.api_base_url}{endpoint}"

        if self.dry_run:
            logger.info(f"[DRY RUN] POST {url} data={data}")
            return {"dry_run": True, "method": "POST", "url": url, "data": data}

        self._wait_for_rate_limit()

        logger.debug(f"POST {url}")
        response = self._session.post(
            url,
            json=data,
            headers=self._get_headers(),
            timeout=60,
        )

        return self._handle_response(response)

    def put(
        self,
        endpoint: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Make PUT request to Yahoo DSP API.

        Args:
            endpoint: API endpoint path
            data: Request body data

        Returns:
            Parsed JSON response

        Raises:
            YahooDSPAPIError: For API errors
        """
        # Ensure endpoint starts with /
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
            
        url = f"{self.api_base_url}{endpoint}"

        if self.dry_run:
            logger.info(f"[DRY RUN] PUT {url} data={data}")
            return {"dry_run": True, "method": "PUT", "url": url, "data": data}

        self._wait_for_rate_limit()

        logger.debug(f"PUT {url}")
        response = self._session.put(
            url,
            json=data,
            headers=self._get_headers(),
            timeout=60,
        )

        return self._handle_response(response)

    def delete(
        self,
        endpoint: str,
    ) -> dict[str, Any]:
        """Make DELETE request to Yahoo DSP API.

        Args:
            endpoint: API endpoint path

        Returns:
            Parsed JSON response

        Raises:
            YahooDSPAPIError: For API errors
        """
        # Ensure endpoint starts with /
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"
            
        url = f"{self.api_base_url}{endpoint}"

        if self.dry_run:
            logger.info(f"[DRY RUN] DELETE {url}")
            return {"dry_run": True, "method": "DELETE", "url": url}

        self._wait_for_rate_limit()

        logger.debug(f"DELETE {url}")
        response = self._session.delete(
            url,
            headers=self._get_headers(),
            timeout=60,
        )

        return self._handle_response(response)

    def test_connection(self) -> tuple[bool, str]:
        """Test API connection by fetching dictionary endpoint.

        Returns:
            Tuple of (success, message)
        """
        try:
            # Use dictionary endpoint - it's lightweight and always works
            result = self.get("/traffic/dictionary")
            if result.get("response"):
                return True, "Successfully connected to Yahoo DSP API"
            return False, "Connected but received empty response"
        except YahooDSPAuthError as e:
            return False, f"Authentication failed: {e}"
        except YahooDSPAPIError as e:
            return False, f"API error: {e}"
        except Exception as e:
            return False, f"Connection failed: {e}"
