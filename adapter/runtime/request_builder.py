"""
Request builder for constructing HTTP requests from canonical endpoints.

Handles path parameter substitution, query parameter encoding, header
construction, and request body formatting.
"""

import json
from typing import Any, Dict, Optional, List
from urllib.parse import urlencode

from ..parsing.canonical_models import CanonicalEndpoint, ParameterLocation


class RequestBuilderError(Exception):
    """Error raised when building a request fails."""

    pass


class RequestBuilder:
    """
    Builds HTTP requests from canonical endpoints and parameters.

    This class handles:
    - Path parameter substitution ({id} → actual value)
    - Query parameter encoding
    - Header construction
    - Request body formatting (JSON, form-encoded, etc.)

    Examples:
        >>> from adapter.parsing import Normalizer
        >>> from adapter.ingestion import OpenAPILoader
        >>>
        >>> # Load endpoint
        >>> loader = OpenAPILoader()
        >>> spec = loader.load("openapi.yaml")
        >>> normalizer = Normalizer()
        >>> endpoints = normalizer.normalize_openapi(spec)
        >>>
        >>> # Build request
        >>> builder = RequestBuilder(base_url="https://api.example.com")
        >>> request = builder.build_request(
        ...     endpoint=endpoints[0],
        ...     parameters={"user_id": "123", "include": "profile"}
        ... )
        >>> print(request["url"])  # https://api.example.com/users/123?include=profile
    """

    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize the request builder.

        Args:
            base_url: Optional base URL to prepend to all paths
                     (e.g., "https://api.example.com")
        """
        self.base_url = base_url.rstrip("/") if base_url else None

    def build_request(
        self,
        endpoint: CanonicalEndpoint,
        parameters: Optional[Dict[str, Any]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Build an HTTP request from a canonical endpoint.

        Args:
            endpoint: The canonical endpoint definition
            parameters: Parameter values (name → value)
            extra_headers: Additional headers to include

        Returns:
            Dictionary with request details:
            {
                "method": "GET",
                "url": "https://api.example.com/users/123",
                "headers": {"Content-Type": "application/json"},
                "body": {...} or None,
                "query_params": {"key": "value"}
            }

        Raises:
            RequestBuilderError: If required parameters are missing or invalid
        """
        parameters = parameters or {}
        extra_headers = extra_headers or {}

        # Separate parameters by location
        path_params = {}
        query_params = {}
        headers = {}
        body_params = {}
        cookie_params = {}

        # For POST/PUT/PATCH, parameters should go in body unless explicitly marked otherwise
        # This handles APIs that don't explicitly mark parameters as "body" in OpenAPI spec
        request_uses_body = endpoint.method in ("POST", "PUT", "PATCH")

        for param in endpoint.parameters:
            param_name = param.name
            param_value = parameters.get(param_name)

            # Check required parameters
            if param.required and param_value is None:
                raise RequestBuilderError(
                    f"Missing required parameter '{param_name}' for endpoint '{endpoint.name}'"
                )

            # Skip optional parameters that aren't provided
            if param_value is None:
                continue

            # Route parameter to correct location
            if param.location == ParameterLocation.PATH:
                path_params[param_name] = param_value
            elif param.location == ParameterLocation.HEADER:
                headers[param_name] = str(param_value)
            elif param.location == ParameterLocation.COOKIE:
                cookie_params[param_name] = param_value
            elif param.location == ParameterLocation.BODY:
                body_params[param_name] = param_value
            elif param.location == ParameterLocation.QUERY:
                # For POST/PUT/PATCH, query params should go in body unless explicitly marked as query
                if request_uses_body:
                    body_params[param_name] = param_value
                else:
                    query_params[param_name] = param_value
            else:
                # Default behavior: POST/PUT/PATCH -> body, GET/DELETE -> query
                if request_uses_body:
                    body_params[param_name] = param_value
                else:
                    query_params[param_name] = param_value

        # Also add any parameters not in endpoint definition to body for POST/PUT/PATCH
        if request_uses_body:
            endpoint_param_names = {p.name for p in endpoint.parameters}
            for param_name, param_value in parameters.items():
                if param_name not in endpoint_param_names and param_value is not None:
                    body_params[param_name] = param_value

        # Build URL with path parameters
        url = self._build_url(endpoint.path, path_params)

        # Add extra headers
        headers.update(extra_headers)

        # Build request body
        body = self._build_body(body_params, endpoint) if body_params else None

        # Add cookies to headers if any
        if cookie_params:
            cookie_header = "; ".join([f"{k}={v}" for k, v in cookie_params.items()])
            if "Cookie" in headers:
                headers["Cookie"] += f"; {cookie_header}"
            else:
                headers["Cookie"] = cookie_header

        return {
            "method": endpoint.method,
            "url": url,
            "headers": headers,
            "body": body,
            "query_params": query_params,
        }

    def _build_url(self, path: str, path_params: Dict[str, Any]) -> str:
        """
        Build the full URL with path parameter substitution.

        Args:
            path: The path template (e.g., "/users/{user_id}")
            path_params: Path parameter values

        Returns:
            Complete URL with parameters substituted

        Raises:
            RequestBuilderError: If required path parameters are missing
        """
        # Substitute path parameters
        url_path = path
        for param_name, param_value in path_params.items():
            placeholder = f"{{{param_name}}}"
            if placeholder not in url_path:
                raise RequestBuilderError(
                    f"Path parameter '{param_name}' not found in path '{path}'"
                )
            url_path = url_path.replace(placeholder, str(param_value))

        # Check for unsubstituted placeholders
        import re

        remaining_placeholders = re.findall(r"\{(\w+)\}", url_path)
        if remaining_placeholders:
            raise RequestBuilderError(
                f"Missing required path parameters: {', '.join(remaining_placeholders)}"
            )

        # Combine with base URL if provided
        if self.base_url:
            # Ensure path starts with /
            if not url_path.startswith("/"):
                url_path = "/" + url_path
            return self.base_url + url_path

        return url_path

    def _build_body(
        self, body_params: Dict[str, Any], endpoint: CanonicalEndpoint
    ) -> Optional[Any]:
        """
        Build the request body from body parameters.

        Args:
            body_params: Body parameter values
            endpoint: The canonical endpoint (for content type hints)

        Returns:
            Request body (dict, string, or None)
        """
        if not body_params:
            return None

        # For now, default to JSON body
        # Future: Support form-encoded, multipart, etc. based on endpoint schema
        return body_params

    def build_from_flat_params(
        self,
        endpoint: CanonicalEndpoint,
        flat_params: Dict[str, Any],
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Build request from flat parameters (all at the same level).

        This is useful when working with MCP tools that have flat parameter schemas.

        Args:
            endpoint: The canonical endpoint definition
            flat_params: Flat parameter dictionary
            extra_headers: Additional headers to include

        Returns:
            Request dictionary
        """
        return self.build_request(endpoint, flat_params, extra_headers)

    def build_from_grouped_params(
        self,
        endpoint: CanonicalEndpoint,
        grouped_params: Dict[str, Dict[str, Any]],
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Build request from grouped parameters (grouped by location).

        This is useful when working with MCP tools that have grouped parameter schemas.

        Args:
            endpoint: The canonical endpoint definition
            grouped_params: Parameters grouped by location
                          e.g., {"path": {"id": 123}, "query": {"filter": "active"}}
            extra_headers: Additional headers to include

        Returns:
            Request dictionary
        """
        # Flatten grouped parameters
        flat_params = {}
        for location, params in grouped_params.items():
            if isinstance(params, dict):
                flat_params.update(params)

        return self.build_request(endpoint, flat_params, extra_headers)
