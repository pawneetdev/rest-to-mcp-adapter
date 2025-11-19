"""
Tool provider for MCP server.

Manages the registry of available tools and provides tool discovery.
Bridges Phase 2 (MCP tools) with the MCP server.
"""

import logging
from typing import List, Dict, Any, Optional

from ..mcp import ToolRegistry, MCPTool

logger = logging.getLogger(__name__)


class ToolProvider:
    """
    Provides tool discovery and metadata for the MCP server.

    This class bridges the gap between Phase 2 (tool generation) and
    Phase 4 (MCP server). It takes a ToolRegistry and exposes tools
    in the format expected by MCP clients.

    Examples:
        >>> from adapter.mcp import ToolRegistry, ToolGenerator
        >>> from adapter.parsing import Normalizer
        >>>
        >>> # Generate tools (Phase 2)
        >>> generator = ToolGenerator()
        >>> tools = generator.generate_tools(endpoints)
        >>> registry = ToolRegistry(name="My API")
        >>> registry.add_tools(tools)
        >>>
        >>> # Create tool provider for MCP server
        >>> provider = ToolProvider(registry)
        >>> tools_list = provider.list_tools()
    """

    def __init__(self, tool_registry: ToolRegistry):
        """
        Initialize the tool provider.

        Args:
            tool_registry: ToolRegistry containing MCP tools from Phase 2
        """
        self.registry = tool_registry
        logger.info(f"ToolProvider initialized with {tool_registry.count()} tools")

    def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools in MCP format.

        Returns:
            List of tool definitions compatible with MCP protocol

        The format follows MCP's tool schema:
        {
            "name": "tool_name",
            "description": "What the tool does",
            "inputSchema": {...}  # JSON Schema for parameters
        }
        """
        tools = []

        for tool in self.registry.get_all_tools():
            tool_dict = {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
            }

            tools.append(tool_dict)

        logger.debug(f"Listed {len(tools)} tools")
        return tools

    def get_tool(self, tool_name: str) -> Optional[MCPTool]:
        """
        Get a specific tool by name.

        Args:
            tool_name: Name of the tool to retrieve

        Returns:
            MCPTool object if found, None otherwise
        """
        tool = self.registry.get_tool(tool_name)

        if tool:
            logger.debug(f"Found tool: {tool_name}")
        else:
            logger.warning(f"Tool not found: {tool_name}")

        return tool

    def get_tool_count(self) -> int:
        """
        Get the total number of available tools.

        Returns:
            Number of tools
        """
        return self.registry.count()

    def search_tools(self, query: str) -> List[MCPTool]:
        """
        Search for tools by name or description.

        Args:
            query: Search query

        Returns:
            List of matching tools
        """
        results = self.registry.search_tools(query)
        logger.debug(f"Search for '{query}' returned {len(results)} results")
        return results

    def get_tools_by_tag(self, tag: str) -> List[MCPTool]:
        """
        Get tools by tag.

        Args:
            tag: Tag to filter by

        Returns:
            List of tools with the specified tag
        """
        results = self.registry.get_tools_by_tag(tag)
        logger.debug(f"Found {len(results)} tools with tag '{tag}'")
        return results

    def get_tool_metadata(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata for a specific tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool metadata (REST endpoint info, etc.) or None if not found
        """
        tool = self.get_tool(tool_name)

        if tool and tool.metadata:
            return tool.metadata

        return None
