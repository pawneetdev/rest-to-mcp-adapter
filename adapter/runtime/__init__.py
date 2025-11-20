"""
Runtime execution engine for REST API calls.

This module provides the ability to execute REST API calls using canonical
endpoints or MCP tool definitions. It handles authentication, request building,
execution, and response processing.
"""

from .auth import (
    AuthHandler,
    NoAuth,
    APIKeyAuth,
    BearerAuth,
    BasicAuth,
    OAuth2Auth,
)
from .executor import APIExecutor, ExecutionResult
from .request_builder import RequestBuilder
from .response import ResponseProcessor, ProcessedResponse

__all__ = [
    "AuthHandler",
    "NoAuth",
    "APIKeyAuth",
    "BearerAuth",
    "BasicAuth",
    "OAuth2Auth",
    "APIExecutor",
    "ExecutionResult",
    "RequestBuilder",
    "ResponseProcessor",
    "ProcessedResponse",
]
