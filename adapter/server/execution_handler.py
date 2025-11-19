"""
Execution handler for MCP server.

Handles tool execution by integrating with Phase 3's runtime executor.
Maps MCP tool calls to actual REST API requests.
"""

import logging
from typing import Any, Dict, Optional

from ..runtime import APIExecutor
from ..parsing.canonical_models import CanonicalEndpoint
from .tool_provider import ToolProvider

logger = logging.getLogger(__name__)


class ExecutionHandler:
    """
    Handles tool execution for the MCP server.

    This class bridges Phase 3 (runtime execution) with Phase 4 (MCP server).
    It takes tool execution requests from MCP clients and uses the APIExecutor
    to make actual REST API calls.

    Examples:
        >>> from adapter.runtime import APIExecutor, BearerAuth
        >>> from adapter.server import ToolProvider, ExecutionHandler
        >>>
        >>> # Set up executor (Phase 3)
        >>> executor = APIExecutor(
        ...     base_url="https://api.example.com",
        ...     auth=BearerAuth(token="token")
        ... )
        >>>
        >>> # Create execution handler
        >>> handler = ExecutionHandler(
        ...     tool_provider=provider,
        ...     executor=executor,
        ...     endpoints=endpoints  # From Phase 1
        ... )
        >>>
        >>> # Execute a tool
        >>> result = handler.execute_tool(
        ...     tool_name="get_user_by_id",
        ...     arguments={"user_id": "123"}
        ... )
    """

    def __init__(
        self,
        tool_provider: ToolProvider,
        executor: APIExecutor,
        endpoints: list,  # List[CanonicalEndpoint]
    ):
        """
        Initialize the execution handler.

        Args:
            tool_provider: ToolProvider for tool lookup
            executor: APIExecutor from Phase 3 for making API calls
            endpoints: List of CanonicalEndpoint objects from Phase 1
        """
        self.tool_provider = tool_provider
        self.executor = executor
        self.endpoints = endpoints

        # Create a mapping from tool name to endpoint
        self._tool_endpoint_map = {}
        self._build_tool_endpoint_map()

        logger.info(
            f"ExecutionHandler initialized with {len(self.endpoints)} endpoints"
        )

    def _build_tool_endpoint_map(self):
        """
        Build a mapping from tool names to canonical endpoints.

        This allows fast lookup when executing a tool by name.
        """
        for tool in self.tool_provider.registry.get_all_tools():
            # Find matching endpoint
            # Tool names follow pattern: {api_name}_{endpoint_name}
            # We need to match against endpoint.name

            for endpoint in self.endpoints:
                # Simple match: if endpoint name is in tool name
                if endpoint.name in tool.name:
                    self._tool_endpoint_map[tool.name] = endpoint
                    break

        logger.debug(f"Built tool→endpoint map with {len(self._tool_endpoint_map)} entries")

    def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool by name with given arguments.

        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments (parameter values)

        Returns:
            Execution result in MCP format:
            {
                "content": [
                    {
                        "type": "text",
                        "text": "result data"
                    }
                ],
                "isError": false
            }

        Raises:
            ValueError: If tool not found or execution fails
        """
        logger.info(f"Executing tool: {tool_name}")
        logger.debug(f"Arguments: {arguments}")

        # Get the tool
        tool = self.tool_provider.get_tool(tool_name)
        if not tool:
            error_msg = f"Tool not found: {tool_name}"
            logger.error(error_msg)
            return self._create_error_result(error_msg)

        # Get the corresponding endpoint
        endpoint = self._tool_endpoint_map.get(tool_name)
        if not endpoint:
            error_msg = f"No endpoint found for tool: {tool_name}"
            logger.error(error_msg)
            return self._create_error_result(error_msg)

        try:
            # Execute the API call using Phase 3 executor
            result = self.executor.execute(
                endpoint=endpoint, parameters=arguments
            )

            # Convert to MCP result format
            if result.success:
                return self._create_success_result(result)
            else:
                return self._create_error_result(
                    result.response.error or "Execution failed"
                )

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            return self._create_error_result(str(e))

    def _create_success_result(self, execution_result) -> Dict[str, Any]:
        """
        Create a successful MCP result from an execution result.

        Args:
            execution_result: ExecutionResult from Phase 3

        Returns:
            MCP-formatted success result
        """
        import json

        # Format the response data as text
        data = execution_result.response.data

        if isinstance(data, (dict, list)):
            text_content = json.dumps(data, indent=2)
        else:
            text_content = str(data)

        # Add execution metadata
        metadata_text = (
            f"\n\n---\n"
            f"Execution Time: {execution_result.execution_time_ms:.2f}ms\n"
            f"Status Code: {execution_result.response.status_code}\n"
            f"Attempts: {execution_result.attempts}"
        )

        return {
            "content": [
                {
                    "type": "text",
                    "text": text_content + metadata_text,
                }
            ],
            "isError": False,
        }

    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """
        Create an error MCP result.

        Args:
            error_message: Error message

        Returns:
            MCP-formatted error result
        """
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"Error: {error_message}",
                }
            ],
            "isError": True,
        }

    def get_endpoint_for_tool(self, tool_name: str) -> Optional[CanonicalEndpoint]:
        """
        Get the canonical endpoint for a given tool name.

        Args:
            tool_name: Tool name

        Returns:
            CanonicalEndpoint if found, None otherwise
        """
        return self._tool_endpoint_map.get(tool_name)
