"""
API executor for executing REST API calls.

Orchestrates request building, authentication, HTTP execution, retries,
and response processing.
"""

import time
import json
import logging
from typing import Any, Dict, Optional
from dataclasses import dataclass

import requests
from requests.exceptions import RequestException, Timeout, ConnectionError

from ..parsing.canonical_models import CanonicalEndpoint
from .auth import AuthHandler, NoAuth
from .request_builder import RequestBuilder
from .response import ResponseProcessor, ProcessedResponse

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """
    Result of executing an API call.

    Attributes:
        endpoint_name: Name of the endpoint that was called
        success: Whether the execution was successful
        response: Processed response
        request_details: Details of the request that was sent
        execution_time_ms: Execution time in milliseconds
        attempts: Number of attempts made (for retries)
    """

    endpoint_name: str
    success: bool
    response: ProcessedResponse
    request_details: Dict[str, Any]
    execution_time_ms: float
    attempts: int = 1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "endpoint_name": self.endpoint_name,
            "success": self.success,
            "response": self.response.to_dict(),
            "request_details": self.request_details,
            "execution_time_ms": self.execution_time_ms,
            "attempts": self.attempts,
        }


class APIExecutor:
    """
    Executes REST API calls with authentication, retries, and error handling.

    Orchestrates all the components to execute actual HTTP requests against
    REST APIs.

    Features:
    - Build requests from canonical endpoints
    - Apply authentication
    - Execute HTTP requests
    - Retry on transient failures
    - Process and parse responses
    - Detailed error reporting

    Examples:
        >>> from adapter.ingestion import OpenAPILoader
        >>> from adapter.parsing import Normalizer
        >>> from adapter.runtime import APIExecutor, BearerAuth
        >>>
        >>> # Load and normalize
        >>> loader = OpenAPILoader()
        >>> spec = loader.load("https://api.example.com/openapi.json")
        >>> normalizer = Normalizer()
        >>> endpoints = normalizer.normalize_openapi(spec)
        >>>
        >>> # Execute API call
        >>> auth = BearerAuth(token="your-token")
        >>> executor = APIExecutor(
        ...     base_url="https://api.example.com",
        ...     auth=auth
        ... )
        >>>
        >>> result = executor.execute(
        ...     endpoint=endpoints[0],
        ...     parameters={"user_id": "123"}
        ... )
        >>>
        >>> if result.success:
        ...     print(result.response.data)
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        auth: Optional[AuthHandler] = None,
        timeout: int = 30,
        max_retries: int = 3,
        retry_backoff: float = 1.0,
        retry_on_status_codes: Optional[list] = None,
    ):
        """
        Initialize the API executor.

        Args:
            base_url: Base URL for all API calls (e.g., "https://api.example.com")
            auth: Authentication handler (default: no auth)
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_backoff: Initial backoff time in seconds (doubles on each retry)
            retry_on_status_codes: HTTP status codes to retry on
                                  (default: [429, 500, 502, 503, 504])
        """
        self.base_url = base_url
        self.auth = auth or NoAuth()
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_backoff = retry_backoff
        self.retry_on_status_codes = retry_on_status_codes or [429, 500, 502, 503, 504]

        self.request_builder = RequestBuilder(base_url=base_url)
        self.response_processor = ResponseProcessor()

    def execute(
        self,
        endpoint: CanonicalEndpoint,
        parameters: Optional[Dict[str, Any]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> ExecutionResult:
        """
        Execute an API call for the given endpoint.

        Args:
            endpoint: Canonical endpoint to call
            parameters: Parameter values for the endpoint
            extra_headers: Additional headers to include

        Returns:
            Execution result with response data

        Raises:
            RequestException: If the request fails after all retries
        """
        start_time = time.time()
        attempts = 0
        last_exception = None

        # Build the request
        try:
            request_details = self.request_builder.build_request(
                endpoint=endpoint,
                parameters=parameters,
                extra_headers=extra_headers,
            )
        except Exception as e:
            # Request building failed
            elapsed_ms = (time.time() - start_time) * 1000
            return ExecutionResult(
                endpoint_name=endpoint.name,
                success=False,
                response=ProcessedResponse(
                    status_code=0,
                    success=False,
                    error=f"Failed to build request: {str(e)}",
                ),
                request_details={},
                execution_time_ms=elapsed_ms,
                attempts=0,
            )

        # Apply authentication (only if endpoint requires it)
        headers = request_details["headers"].copy()
        query_params = request_details["query_params"].copy()

        # Check if endpoint requires authentication
        # If security is empty/None, endpoint is public and doesn't need auth
        requires_auth = endpoint.security and len(endpoint.security) > 0

        if requires_auth:
            logger.debug(f"Endpoint requires authentication: {endpoint.name}")
            self.auth.apply(headers, query_params)
        else:
            logger.debug(f"Endpoint is public (no auth required): {endpoint.name}")

        # Log request details for debugging
        logger.debug(f"Request URL: {request_details['url']}")
        logger.debug(f"Request Method: {request_details['method']}")
        logger.debug(f"Request Headers: {headers}")
        logger.debug(f"Request Body: {request_details['body']}")

        # Execute with retries
        for attempt in range(1, self.max_retries + 1):
            attempts = attempt

            try:
                response = self._execute_http_request(
                    method=request_details["method"],
                    url=request_details["url"],
                    headers=headers,
                    params=query_params,
                    body=request_details["body"],
                )

                # Process response
                processed_response = self.response_processor.process(response)

                elapsed_ms = (time.time() - start_time) * 1000

                # Check if we should retry based on status code
                if (
                    not processed_response.success
                    and processed_response.status_code in self.retry_on_status_codes
                    and attempt < self.max_retries
                ):
                    # Retry with backoff
                    backoff_time = self.retry_backoff * (2 ** (attempt - 1))
                    time.sleep(backoff_time)
                    continue

                # Return result (success or non-retryable failure)
                return ExecutionResult(
                    endpoint_name=endpoint.name,
                    success=processed_response.success,
                    response=processed_response,
                    request_details=request_details,
                    execution_time_ms=elapsed_ms,
                    attempts=attempts,
                )

            except (Timeout, ConnectionError) as e:
                last_exception = e

                # Retry on network errors
                if attempt < self.max_retries:
                    backoff_time = self.retry_backoff * (2 ** (attempt - 1))
                    time.sleep(backoff_time)
                    continue

                # Max retries reached
                break

            except RequestException as e:
                # Non-retryable request error
                last_exception = e
                break

        # All retries exhausted or non-retryable error
        elapsed_ms = (time.time() - start_time) * 1000

        error_message = f"Request failed after {attempts} attempts"
        if last_exception:
            error_message += f": {str(last_exception)}"

        return ExecutionResult(
            endpoint_name=endpoint.name,
            success=False,
            response=ProcessedResponse(
                status_code=0,
                success=False,
                error=error_message,
            ),
            request_details=request_details,
            execution_time_ms=elapsed_ms,
            attempts=attempts,
        )

    def _execute_http_request(
        self,
        method: str,
        url: str,
        headers: Dict[str, str],
        params: Dict[str, Any],
        body: Optional[Any],
    ) -> requests.Response:
        """
        Execute the actual HTTP request.

        Args:
            method: HTTP method
            url: Full URL
            headers: Request headers
            params: Query parameters
            body: Request body

        Returns:
            Response object
        """
        # Prepare request kwargs
        kwargs = {
            "timeout": self.timeout,
            "headers": headers,
            "params": params,
        }

        # Add body if present
        if body is not None:
            # If body is a dict, send as JSON
            if isinstance(body, dict):
                kwargs["json"] = body
                # Ensure Content-Type is set
                if "Content-Type" not in headers:
                    headers["Content-Type"] = "application/json"
            else:
                kwargs["data"] = body

        # Execute request
        return requests.request(method=method, url=url, **kwargs)

    def execute_batch(
        self,
        calls: list,
    ) -> list:
        """
        Execute multiple API calls in sequence.

        Args:
            calls: List of (endpoint, parameters) tuples

        Returns:
            List of execution results
        """
        results = []

        for endpoint, parameters in calls:
            result = self.execute(endpoint=endpoint, parameters=parameters)
            results.append(result)

        return results
