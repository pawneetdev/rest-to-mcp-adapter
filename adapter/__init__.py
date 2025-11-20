"""
Universal REST → MCP Adapter

A production-quality framework for converting REST API documentation
into MCP-compatible tools for Large Language Models and agent systems.

This package provides:
- Format detection for various API documentation formats
- Extensible loader framework for ingesting API specs
- Canonical data models for normalized endpoint representation
- Normalization layer for consistent data transformation
"""

__version__ = "0.1.0"

# Phase 1: Ingestion & Parsing
from .ingestion import OpenAPILoader, BaseLoader
from .parsing import Normalizer, CanonicalEndpoint, CanonicalParameter, CanonicalSchema

# Phase 2: MCP Tools
from .mcp import ToolGenerator, ToolRegistry, MCPTool, SchemaConverter

# Phase 3: Runtime Execution
from .runtime import (
    APIExecutor,
    RequestBuilder,
    ResponseProcessor,
    AuthHandler,
    NoAuth,
    APIKeyAuth,
    BearerAuth,
    BasicAuth,
    OAuth2Auth,
    ExecutionResult,
    ProcessedResponse,
)

# Phase 4: MCP Server
from .server import MCPServer, ToolProvider, ExecutionHandler, StdioTransport

__all__ = [
    # Version
    "__version__",
    # Phase 1
    "OpenAPILoader",
    "BaseLoader",
    "Normalizer",
    "CanonicalEndpoint",
    "CanonicalParameter",
    "CanonicalSchema",
    # Phase 2
    "ToolGenerator",
    "ToolRegistry",
    "MCPTool",
    "SchemaConverter",
    # Phase 3
    "APIExecutor",
    "RequestBuilder",
    "ResponseProcessor",
    "AuthHandler",
    "NoAuth",
    "APIKeyAuth",
    "BearerAuth",
    "BasicAuth",
    "OAuth2Auth",
    "ExecutionResult",
    "ProcessedResponse",
    # Phase 4
    "MCPServer",
    "ToolProvider",
    "ExecutionHandler",
    "StdioTransport",
]
