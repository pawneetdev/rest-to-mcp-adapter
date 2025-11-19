"""
Tool registry for managing MCP tools.

Provides functionality to organize, filter, and export MCP tool definitions.
The registry acts as a central manager for all generated tools.
"""

import json
from typing import Any, Dict, List, Optional, Set

from .tool_generator import MCPTool


class ToolRegistry:
    """
    Registry for managing MCP tools.

    The registry provides:
    - Storage and organization of MCP tools
    - Filtering by tags, names, or other criteria
    - Export to various formats (JSON, dict)
    - Duplicate detection and management

    Examples:
        >>> from adapter.mcp import ToolRegistry, ToolGenerator
        >>> from adapter.parsing import Normalizer
        >>>
        >>> # Generate tools
        >>> generator = ToolGenerator()
        >>> tools = generator.generate_tools(endpoints)
        >>>
        >>> # Create registry
        >>> registry = ToolRegistry()
        >>> registry.add_tools(tools)
        >>>
        >>> # Filter tools
        >>> user_tools = registry.get_tools_by_tag("users")
        >>> print(f"Found {len(user_tools)} user-related tools")
        >>>
        >>> # Export to JSON
        >>> with open("tools.json", "w") as f:
        ...     registry.export_json(f)
    """

    def __init__(self, name: Optional[str] = None):
        """
        Initialize the tool registry.

        Args:
            name: Optional name for the registry (e.g., API name)
        """
        self.name = name
        self._tools: Dict[str, MCPTool] = {}

    def add_tool(self, tool: MCPTool) -> None:
        """
        Add a tool to the registry.

        Args:
            tool: MCP tool to add

        Raises:
            ValueError: If a tool with the same name already exists
        """
        if tool.name in self._tools:
            raise ValueError(
                f"Tool '{tool.name}' already exists in registry. "
                f"Use update_tool() to modify existing tools."
            )

        self._tools[tool.name] = tool

    def add_tools(self, tools: List[MCPTool]) -> None:
        """
        Add multiple tools to the registry.

        Args:
            tools: List of MCP tools to add

        Raises:
            ValueError: If any tool name already exists
        """
        for tool in tools:
            self.add_tool(tool)

    def update_tool(self, tool: MCPTool) -> None:
        """
        Update an existing tool in the registry.

        Args:
            tool: Updated tool

        Raises:
            KeyError: If tool doesn't exist
        """
        if tool.name not in self._tools:
            raise KeyError(
                f"Tool '{tool.name}' not found in registry. "
                f"Use add_tool() to add new tools."
            )

        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[MCPTool]:
        """
        Get a tool by name.

        Args:
            name: Tool name

        Returns:
            MCP tool or None if not found
        """
        return self._tools.get(name)

    def get_all_tools(self) -> List[MCPTool]:
        """
        Get all tools in the registry.

        Returns:
            List of all MCP tools
        """
        return list(self._tools.values())

    def get_tool_names(self) -> List[str]:
        """
        Get all tool names in the registry.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def get_tools_by_tag(self, tag: str) -> List[MCPTool]:
        """
        Get all tools with a specific tag.

        Args:
            tag: Tag to filter by

        Returns:
            List of tools with the tag
        """
        tools = []
        for tool in self._tools.values():
            if tool.metadata and "tags" in tool.metadata:
                if tag in tool.metadata["tags"]:
                    tools.append(tool)

        return tools

    def get_tools_by_method(self, method: str) -> List[MCPTool]:
        """
        Get all tools for a specific HTTP method.

        Args:
            method: HTTP method (GET, POST, etc.)

        Returns:
            List of tools with the method
        """
        method = method.upper()
        tools = []

        for tool in self._tools.values():
            if tool.metadata and tool.metadata.get("method") == method:
                tools.append(tool)

        return tools

    def search_tools(self, query: str) -> List[MCPTool]:
        """
        Search tools by name or description.

        Args:
            query: Search query (case-insensitive)

        Returns:
            List of matching tools
        """
        query_lower = query.lower()
        tools = []

        for tool in self._tools.values():
            # Search in name
            if query_lower in tool.name.lower():
                tools.append(tool)
                continue

            # Search in description
            if query_lower in tool.description.lower():
                tools.append(tool)
                continue

        return tools

    def get_all_tags(self) -> Set[str]:
        """
        Get all unique tags across all tools.

        Returns:
            Set of all tags
        """
        tags = set()

        for tool in self._tools.values():
            if tool.metadata and "tags" in tool.metadata:
                tags.update(tool.metadata["tags"])

        return tags

    def remove_tool(self, name: str) -> bool:
        """
        Remove a tool from the registry.

        Args:
            name: Tool name

        Returns:
            True if tool was removed, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            return True
        return False

    def clear(self) -> None:
        """Remove all tools from the registry."""
        self._tools.clear()

    def count(self) -> int:
        """
        Get the number of tools in the registry.

        Returns:
            Number of tools
        """
        return len(self._tools)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert registry to dictionary format.

        Returns:
            Dictionary representation of the registry
        """
        result = {
            "name": self.name,
            "tools": [tool.to_dict() for tool in self._tools.values()],
            "count": len(self._tools),
        }

        # Add metadata
        result["metadata"] = {
            "tags": list(self.get_all_tags()),
            "tool_names": self.get_tool_names(),
        }

        return result

    def to_json(self, indent: int = 2) -> str:
        """
        Convert registry to JSON string.

        Args:
            indent: JSON indentation level

        Returns:
            JSON string representation
        """
        return json.dumps(self.to_dict(), indent=indent)

    def export_json(self, file_path: str, indent: int = 2) -> None:
        """
        Export registry to a JSON file.

        Args:
            file_path: Path to output file
            indent: JSON indentation level

        Examples:
            >>> registry.export_json("tools.json")
        """
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.to_json(indent=indent))

    def export_tools_only(self, file_path: str, indent: int = 2) -> None:
        """
        Export only the tools array to a JSON file.

        This is useful when you need just the tools without metadata.

        Args:
            file_path: Path to output file
            indent: JSON indentation level

        Examples:
            >>> registry.export_tools_only("tools_array.json")
        """
        tools_array = [tool.to_dict() for tool in self._tools.values()]

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(tools_array, f, indent=indent)

    def __len__(self) -> int:
        """Return the number of tools in the registry."""
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        """Check if a tool exists in the registry."""
        return name in self._tools

    def __repr__(self) -> str:
        """String representation of the registry."""
        name_part = f"name='{self.name}', " if self.name else ""
        return f"ToolRegistry({name_part}tools={len(self._tools)})"
