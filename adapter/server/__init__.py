"""
MCP (Model Context Protocol) server implementation.

This module provides a complete MCP server that exposes REST API tools
to LLM agents like Claude. It integrates all previous phases:
- Phase 1: Load and normalize API specs
- Phase 2: Generate MCP tool definitions
- Phase 3: Execute actual API calls

The server implements the MCP protocol over stdio transport.
"""

from .server import MCPServer
from .transport import StdioTransport
from .tool_provider import ToolProvider
from .execution_handler import ExecutionHandler

__all__ = [
    "MCPServer",
    "StdioTransport",
    "ToolProvider",
    "ExecutionHandler",
]
