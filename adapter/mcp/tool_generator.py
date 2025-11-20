"""
MCP tool generator for REST API endpoints.

Converts canonical endpoint models into MCP (Model Context Protocol) tool
definitions that can be used by LLM agents like Claude.

MCP tools follow a specific format with:
- name: Unique identifier for the tool
- description: Human-readable description of what the tool does
- inputSchema: JSON Schema defining the expected inputs
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ..parsing.canonical_models import CanonicalEndpoint
from .schema_converter import SchemaConverter


@dataclass
class MCPTool:
    """
    Represents an MCP tool definition.

    This is the final format that gets sent to MCP-compatible LLM agents.

    Attributes:
        name: Unique tool identifier (snake_case)
        description: Human-readable description
        inputSchema: JSON Schema for tool inputs
        metadata: Additional metadata (method, path, tags, etc.)
    """

    name: str
    description: str
    inputSchema: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary format for JSON serialization."""
        result = {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.inputSchema,
        }

        if self.metadata:
            result["metadata"] = self.metadata

        return result


class ToolGenerator:
    """
    Generates MCP tool definitions from canonical endpoints.

    This is the main class for Phase 2 - it takes normalized API endpoints
    and converts them into MCP-compatible tool definitions.

    Features:
    - Converts endpoint parameters to JSON Schema
    - Generates descriptive tool names and descriptions
    - Includes metadata about the original REST endpoint
    - Handles complex schemas (nested objects, arrays)

    Examples:
        >>> from adapter.parsing import Normalizer
        >>> from adapter.ingestion import OpenAPILoader
        >>>
        >>> # Load and normalize OpenAPI spec
        >>> loader = OpenAPILoader()
        >>> spec = loader.load("openapi.yaml")
        >>> normalizer = Normalizer()
        >>> endpoints = normalizer.normalize_openapi(spec)
        >>>
        >>> # Generate MCP tools
        >>> generator = ToolGenerator()
        >>> tools = generator.generate_tools(endpoints)
        >>>
        >>> for tool in tools:
        ...     print(f"Tool: {tool.name}")
        ...     print(f"Description: {tool.description}")
    """

    # Default authentication parameters that are commonly used across APIs
    # These will be filtered from tool schemas by default
    DEFAULT_AUTH_PARAMS = {
        'signature', 'timestamp', 'recvwindow', 'recv_window',
        'api_key', 'apikey', 'api_secret', 'apisecret',
        'access_token', 'accesstoken', 'token',
        'authorization', 'auth',
        'nonce', 'sign',
    }

    def __init__(
        self,
        include_metadata: bool = True,
        group_parameters: bool = False,
        api_name: Optional[str] = None,
        auth_params: Optional[set] = None,
        auto_detected_auth_params: Optional[set] = None,
    ):
        """
        Initialize the tool generator.

        Args:
            include_metadata: Include REST endpoint metadata in tools
            group_parameters: Group parameters by location (path/query/header)
            api_name: Optional API name to prefix tool names
            auth_params: Custom set of auth parameter names to filter (overrides defaults)
                        If None, uses DEFAULT_AUTH_PARAMS + auto_detected_auth_params
                        If provided, completely replaces the default set
            auto_detected_auth_params: Auth params extracted from OpenAPI security schemes
                                      These are merged with defaults unless auth_params overrides

        Examples:
            >>> # Use defaults + auto-detected params
            >>> generator = ToolGenerator()

            >>> # Add custom auth params to defaults
            >>> generator = ToolGenerator(
            ...     auto_detected_auth_params={'custom_auth_header', 'session_id'}
            ... )

            >>> # Completely override with custom params only
            >>> generator = ToolGenerator(
            ...     auth_params={'my_signature', 'my_timestamp'}
            ... )
        """
        self.include_metadata = include_metadata
        self.group_parameters = group_parameters
        self.api_name = api_name
        self.schema_converter = SchemaConverter()

        # Determine which auth parameters to filter
        # Normalize all auth param names: lowercase + convert hyphens to underscores
        # This matches how the Normalizer converts parameter names
        def normalize_auth_param(name: str) -> str:
            return name.lower().replace('-', '_')

        if auth_params is not None:
            # User provided explicit override - use only those
            self.auth_params = {normalize_auth_param(p) for p in auth_params}
        else:
            # Start with defaults
            self.auth_params = {normalize_auth_param(p) for p in self.DEFAULT_AUTH_PARAMS}

            # Merge with auto-detected params from OpenAPI security schemes
            if auto_detected_auth_params:
                self.auth_params.update(normalize_auth_param(p) for p in auto_detected_auth_params)

    def generate_tools(
        self,
        endpoints: List[CanonicalEndpoint],
        limit: Optional[int] = None,
        path_pattern: Optional[str] = None,
        method_filter: Optional[str] = None,
    ) -> List[MCPTool]:
        """
        Generate MCP tools from a list of canonical endpoints.

        Args:
            endpoints: List of normalized endpoints
            limit: Optional maximum number of tools to generate
            path_pattern: Optional regex pattern to filter endpoints by path
            method_filter: Optional HTTP method filter (GET, POST, etc.)

        Returns:
            List of MCP tool definitions

        Examples:
            >>> generator = ToolGenerator()
            >>> # Generate all tools
            >>> tools = generator.generate_tools(endpoints)
            >>>
            >>> # Generate only first 10 tools
            >>> tools = generator.generate_tools(endpoints, limit=10)
            >>>
            >>> # Generate only GET endpoints
            >>> tools = generator.generate_tools(endpoints, method_filter='GET')
            >>>
            >>> # Generate tools for /users path
            >>> tools = generator.generate_tools(endpoints, path_pattern=r'/users')
            >>>
            >>> # Combine filters
            >>> tools = generator.generate_tools(
            ...     endpoints,
            ...     method_filter='GET',
            ...     path_pattern=r'/users',
            ...     limit=5
            ... )
        """
        import re

        tools = []
        count = 0

        # Compile regex if pattern provided
        path_regex = None
        if path_pattern:
            try:
                path_regex = re.compile(path_pattern, re.IGNORECASE)
            except re.error as e:
                raise ValueError(f"Invalid path pattern: {e}")

        # Normalize method filter
        if method_filter:
            method_filter = method_filter.upper()

        for endpoint in endpoints:
            # Apply method filter
            if method_filter and endpoint.method != method_filter:
                continue

            # Apply path pattern filter
            if path_regex and not path_regex.search(endpoint.path):
                continue

            # Generate tool
            tool = self.generate_tool(endpoint)
            tools.append(tool)
            count += 1

            # Apply limit
            if limit is not None and count >= limit:
                break

        return tools

    def generate_tool(
        self,
        endpoint: CanonicalEndpoint,
    ) -> MCPTool:
        """
        Generate an MCP tool from a single canonical endpoint.

        Args:
            endpoint: Canonical endpoint

        Returns:
            MCP tool definition

        Examples:
            >>> generator = ToolGenerator()
            >>> tool = generator.generate_tool(endpoint)
        """
        # Generate tool name
        tool_name = self._generate_tool_name(endpoint)

        # Generate tool description
        description = self._generate_description(endpoint)

        # Generate input schema
        input_schema = self._generate_input_schema(endpoint)

        # Generate metadata
        metadata = self._generate_metadata(endpoint) if self.include_metadata else None

        return MCPTool(
            name=tool_name,
            description=description,
            inputSchema=input_schema,
            metadata=metadata,
        )

    def _generate_tool_name(self, endpoint: CanonicalEndpoint, max_length: int = 64) -> str:
        """
        Generate a unique tool name for the endpoint.

        Tool names must not exceed max_length characters (default 64 for MCP).
        If a name is too long, it will be intelligently truncated.

        Args:
            endpoint: Canonical endpoint
            max_length: Maximum allowed length for tool names (default: 64)

        Returns:
            Tool name (snake_case, <= max_length chars)
        """
        base_name = endpoint.name

        # Optionally prefix with API name
        if self.api_name:
            # Convert API name to snake_case
            api_prefix = self.api_name.lower().replace(" ", "_").replace("-", "_")
            full_name = f"{api_prefix}_{base_name}"
        else:
            full_name = base_name

        # Check if name exceeds max length
        if len(full_name) <= max_length:
            return full_name

        # Name is too long - truncate intelligently
        # Strategy: Keep the prefix, method, and key path components
        # Remove version numbers and intermediate path segments

        parts = full_name.split("_")

        # Keep the API prefix if present
        if self.api_name:
            prefix = parts[0]  # e.g., "binance"
            remaining_parts = parts[1:]
        else:
            prefix = ""
            remaining_parts = parts

        # Keep the HTTP method (first part after prefix)
        method = remaining_parts[0] if remaining_parts else ""
        path_parts = remaining_parts[1:] if len(remaining_parts) > 1 else []

        # Remove version numbers (v1, v2, v3, etc.) and "api" keywords
        filtered_parts = [
            p for p in path_parts
            if not (p.startswith("v") and p[1:].isdigit()) and p not in ("api", "sapi")
        ]

        # Build the truncated name
        if prefix:
            truncated = f"{prefix}_{method}"
        else:
            truncated = method

        # Add path components until we approach the limit
        # Leave room for potential numeric suffix if needed
        available_length = max_length - len(truncated) - 5  # Reserve 5 chars for safety

        for part in filtered_parts:
            if len(truncated) + len(part) + 1 <= max_length - 3:
                truncated += f"_{part}"
            else:
                # Abbreviate the part if it's very long
                if len(part) > 8:
                    truncated += f"_{part[:6]}"
                    break
                else:
                    truncated += f"_{part}"
                    break

        # Final check - if still too long, hard truncate
        if len(truncated) > max_length:
            truncated = truncated[:max_length]

        return truncated

    def _generate_description(self, endpoint: CanonicalEndpoint) -> str:
        """
        Generate a human-readable description for the tool.

        Uses the endpoint's description, summary, or generates one from
        the method and path.

        Args:
            endpoint: Canonical endpoint

        Returns:
            Tool description
        """
        # Try to use existing description
        if endpoint.description:
            desc = endpoint.description.strip()
            # Add method and path info
            desc = f"{desc}\n\nEndpoint: {endpoint.method} {endpoint.path}"
            return desc

        # Try summary
        if endpoint.summary:
            desc = endpoint.summary.strip()
            desc = f"{desc}\n\nEndpoint: {endpoint.method} {endpoint.path}"
            return desc

        # Generate basic description
        return f"Makes a {endpoint.method} request to {endpoint.path}"

    def _generate_input_schema(
        self,
        endpoint: CanonicalEndpoint,
    ) -> Dict[str, Any]:
        """
        Generate JSON Schema for the tool's input parameters.

        Filters out authentication parameters that should be handled by auth handlers,
        not by end users. The set of filtered parameters is configurable via the
        constructor and can include:
        - Default common auth params (signature, timestamp, api_key, etc.)
        - Auto-detected params from OpenAPI security schemes
        - Custom user-provided params

        Args:
            endpoint: Canonical endpoint

        Returns:
            JSON Schema for inputs (with auth params filtered out)
        """
        # Filter out authentication parameters
        filtered_parameters = []
        if endpoint.parameters:
            for param in endpoint.parameters:
                # Skip authentication parameters (case-insensitive comparison)
                if param.name.lower() in self.auth_params:
                    continue
                filtered_parameters.append(param)

        # Convert parameters to JSON Schema
        if filtered_parameters:
            schema = self.schema_converter.parameters_to_json_schema(
                filtered_parameters,
                group_by_location=self.group_parameters,
            )
        else:
            # No parameters - empty object schema
            schema = {
                "type": "object",
                "properties": {},
            }

        # If there's a body schema, add it to the input schema
        if endpoint.body_schema:
            body_json_schema = self.schema_converter.canonical_schema_to_json_schema(
                endpoint.body_schema
            )

            # Add body as a property
            if not self.group_parameters:
                # Flat structure - add body fields directly
                if body_json_schema.get("type") == "object":
                    # Merge body properties into main schema
                    body_props = body_json_schema.get("properties", {})
                    schema["properties"].update(body_props)

                    # Merge required fields
                    body_required = body_json_schema.get("required", [])
                    if body_required:
                        if "required" not in schema:
                            schema["required"] = []
                        schema["required"].extend(body_required)
                else:
                    # Non-object body - add as "body" parameter
                    schema["properties"]["body"] = body_json_schema
                    if "required" not in schema:
                        schema["required"] = []
                    schema["required"].append("body")
            else:
                # Grouped structure - add body as separate group
                schema["properties"]["body"] = body_json_schema
                if "required" not in schema:
                    schema["required"] = []
                schema["required"].append("body")

        return schema

    def _generate_metadata(
        self,
        endpoint: CanonicalEndpoint,
    ) -> Dict[str, Any]:
        """
        Generate metadata about the REST endpoint.

        This metadata can be used by the runtime execution engine
        to make the actual HTTP request.

        Args:
            endpoint: Canonical endpoint

        Returns:
            Metadata dictionary
        """
        metadata = {
            "method": endpoint.method,
            "path": endpoint.path,
        }

        # Add tags if available
        if endpoint.tags:
            metadata["tags"] = endpoint.tags

        # Add deprecation status
        if endpoint.deprecated:
            metadata["deprecated"] = True

        # Add response schema if available
        if endpoint.response_schema:
            response_json_schema = self.schema_converter.canonical_schema_to_json_schema(
                endpoint.response_schema
            )
            metadata["responseSchema"] = response_json_schema

        return metadata
