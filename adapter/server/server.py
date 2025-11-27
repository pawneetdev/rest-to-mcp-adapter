"""
MCP (Model Context Protocol) server implementation.

Main server class that handles JSON-RPC protocol and coordinates
between transport, tool provider, and execution handler.
"""

import logging
from typing import Any, Dict, Optional, List

from .transport import StdioTransport
from .tool_provider import ToolProvider
from .execution_handler import ExecutionHandler

logger = logging.getLogger(__name__)


class MCPServer:
    """
    MCP server implementation.

    Implements the MCP protocol and exposes REST API tools to LLM agents
    like Claude.

    Protocol methods supported:
    - initialize: Server initialization handshake
    - tools/list: List available tools
    - tools/call: Execute a tool

    Examples:
        >>> from adapter.ingestion import OpenAPILoader
        >>> from adapter.parsing import Normalizer
        >>> from adapter.mcp import ToolGenerator, ToolRegistry
        >>> from adapter.runtime import APIExecutor, BearerAuth
        >>> from adapter.server import MCPServer
        >>>
        >>> # Load and normalize
        >>> loader = OpenAPILoader()
        >>> spec = loader.load("https://api.example.com/openapi.json")
        >>> normalizer = Normalizer()
        >>> endpoints = normalizer.normalize_openapi(spec)
        >>>
        >>> # Generate tools
        >>> generator = ToolGenerator(api_name="example")
        >>> tools = generator.generate_tools(endpoints)
        >>> registry = ToolRegistry(name="Example API")
        >>> registry.add_tools(tools)
        >>>
        >>> # Set up executor
        >>> executor = APIExecutor(
        ...     base_url="https://api.example.com",
        ...     auth=BearerAuth(token="token")
        ... )
        >>>
        >>> # Create and run MCP server
        >>> server = MCPServer(
        ...     name="Example API MCP Server",
        ...     version="1.0.0",
        ...     tool_registry=registry,
        ...     executor=executor,
        ...     endpoints=endpoints
        ... )
        >>> server.run()  # Starts stdio server
    """

    def __init__(
        self,
        name: str,
        version: str,
        tool_registry,  # ToolRegistry
        executor,  # APIExecutor
        endpoints: Optional[list] = None,  # List[CanonicalEndpoint] - NOW OPTIONAL!
    ):
        """
        Initialize the MCP server.

        Args:
            name: Server name
            version: Server version
            tool_registry: ToolRegistry (may contain endpoints)
            executor: APIExecutor for making API calls
            endpoints: Optional list of CanonicalEndpoint.
                      If not provided, will be retrieved from tool_registry.

        Raises:
            ValueError: If endpoints not provided and registry doesn't contain endpoints
        """
        self.name = name
        self.version = version

        # Get endpoints from registry if not provided
        if endpoints is None:
            if hasattr(tool_registry, 'get_all_endpoints') and tool_registry.has_endpoints():
                endpoints = tool_registry.get_all_endpoints()
                logger.info("Using endpoints from tool registry")
            else:
                raise ValueError(
                    "No endpoints provided and registry doesn't contain endpoints. "
                    "Either pass endpoints parameter or use ToolRegistry.create_from_openapi()."
                )

        # Initialize components
        self.tool_provider = ToolProvider(tool_registry)
        self.execution_handler = ExecutionHandler(
            tool_provider=self.tool_provider,
            executor=executor,
            endpoints=endpoints,
        )
        self.transport = StdioTransport()

        # Server state
        self.initialized = False

        logger.info(f"MCPServer '{name}' v{version} created")
        logger.info(f"Available tools: {self.tool_provider.get_tool_count()}")

    def run(self):
        """
        Start the MCP server on stdio transport.

        This method blocks until the server is stopped.
        """
        logger.info("Starting MCP server...")
        self.transport.start(message_handler=self.handle_message)

    def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Handle incoming JSON-RPC message.

        Args:
            message: Parsed JSON-RPC message

        Returns:
            JSON-RPC response or None (for notifications)
        """
        # Validate JSON-RPC format
        if "jsonrpc" not in message or message["jsonrpc"] != "2.0":
            return self._create_error_response(
                message_id=message.get("id"),
                code=-32600,
                message="Invalid Request - missing or invalid jsonrpc field",
            )

        method = message.get("method")
        params = message.get("params", {})
        message_id = message.get("id")

        # Check if this is a notification (no id field)
        is_notification = "id" not in message

        if not method:
            if not is_notification:
                return self._create_error_response(
                    message_id=message_id,
                    code=-32600,
                    message="Invalid Request - missing method",
                )
            return None

        logger.debug(f"Handling method: {method} (notification: {is_notification})")

        # Handle notifications (don't send response)
        if method.startswith("notifications/"):
            logger.debug(f"Received notification: {method}")
            # Handle notification but don't respond
            if method == "notifications/initialized":
                logger.info("Client initialized")
            return None

        # Route to appropriate handler (only for requests with id)
        try:
            if method == "initialize":
                result = self.handle_initialize(params)
            elif method == "tools/list":
                result = self.handle_tools_list(params)
            elif method == "tools/call":
                result = self.handle_tools_call(params)
            else:
                if not is_notification:
                    return self._create_error_response(
                        message_id=message_id,
                        code=-32601,
                        message=f"Method not found: {method}",
                    )
                return None

            # Create success response (only for requests, not notifications)
            if not is_notification:
                return {
                    "jsonrpc": "2.0",
                    "id": message_id,
                    "result": result,
                }
            return None

        except Exception as e:
            logger.error(f"Error handling {method}: {e}", exc_info=True)
            if not is_notification:
                return self._create_error_response(
                    message_id=message_id,
                    code=-32603,
                    message="Internal error",
                    data=str(e),
                )
            return None

    def handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle initialize request.

        Args:
            params: Initialize parameters

        Returns:
            Initialize response
        """
        logger.info("Handling initialize request")

        self.initialized = True

        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
            },
            "serverInfo": {
                "name": self.name,
                "version": self.version,
            },
        }

    def handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tools/list request.

        Args:
            params: List parameters (currently unused)

        Returns:
            List of available tools
        """
        logger.info("Handling tools/list request")

        tools = self.tool_provider.list_tools()

        return {
            "tools": tools,
        }

    def handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle tools/call request.

        Args:
            params: Tool call parameters
                   {
                       "name": "tool_name",
                       "arguments": {...}
                   }

        Returns:
            Tool execution result
        """
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if not tool_name:
            raise ValueError("Missing required parameter: name")

        logger.info(f"Handling tools/call request for: {tool_name}")

        result = self.execution_handler.execute_tool(
            tool_name=tool_name, arguments=arguments
        )

        return result

    def _create_error_response(
        self,
        message_id: Optional[Any],
        code: int,
        message: str,
        data: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """
        Create a JSON-RPC error response.

        Args:
            message_id: Original message ID
            code: Error code
            message: Error message
            data: Additional error data

        Returns:
            JSON-RPC error response
        """
        response = {
            "jsonrpc": "2.0",
            "id": message_id,
            "error": {
                "code": code,
                "message": message,
            },
        }

        if data is not None:
            response["error"]["data"] = data

        return response

    def stop(self):
        """Stop the MCP server."""
        logger.info("Stopping MCP server...")
        self.transport.stop()
