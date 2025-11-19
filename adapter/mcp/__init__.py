"""
MCP (Model Context Protocol) layer for tool generation.

This module provides functionality to convert canonical endpoint models
into MCP-compatible tool definitions that can be used by LLM agents.

Key components:
- ToolGenerator: Convert CanonicalEndpoint to MCP tool definitions
- SchemaConverter: Convert canonical schemas to JSON Schema
- ToolRegistry: Manage and organize generated tools
"""

from .schema_converter import SchemaConverter
from .tool_generator import ToolGenerator, MCPTool
from .tool_registry import ToolRegistry

__all__ = [
    "SchemaConverter",
    "ToolGenerator",
    "MCPTool",
    "ToolRegistry",
]
