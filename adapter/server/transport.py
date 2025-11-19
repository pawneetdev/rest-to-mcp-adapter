"""
Transport layer for MCP server.

Handles communication via stdio (standard input/output) following the
MCP protocol specification.
"""

import sys
import json
import logging
from typing import Any, Dict, Optional, Callable

logger = logging.getLogger(__name__)


class StdioTransport:
    """
    Stdio transport for MCP server.

    Reads JSON-RPC messages from stdin and writes responses to stdout.
    Each message is a single line of JSON.

    Examples:
        >>> transport = StdioTransport()
        >>> transport.start(message_handler=handle_message)
    """

    def __init__(self):
        """Initialize stdio transport."""
        self.running = False

    def start(self, message_handler: Callable[[Dict[str, Any]], Dict[str, Any]]):
        """
        Start listening for messages on stdin.

        Args:
            message_handler: Function that processes incoming messages
                           and returns a response

        The handler receives a dict (parsed JSON) and should return a dict
        (JSON-RPC response).
        """
        self.running = True
        logger.info("MCP server started on stdio transport")

        try:
            while self.running:
                # Read one line from stdin
                line = sys.stdin.readline()

                if not line:
                    # EOF reached
                    logger.info("EOF reached, shutting down")
                    break

                line = line.strip()
                if not line:
                    # Empty line, skip
                    continue

                try:
                    # Parse JSON-RPC message
                    message = json.loads(line)
                    logger.debug(f"Received message: {message}")

                    # Process message
                    response = message_handler(message)

                    # Send response
                    if response:
                        self.send_message(response)

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON received: {e}")
                    # Send error response
                    error_response = self._create_error_response(
                        message_id=None,
                        code=-32700,
                        message="Parse error",
                        data=str(e),
                    )
                    self.send_message(error_response)

                except Exception as e:
                    logger.error(f"Error processing message: {e}", exc_info=True)
                    # Send internal error response
                    error_response = self._create_error_response(
                        message_id=None,
                        code=-32603,
                        message="Internal error",
                        data=str(e),
                    )
                    self.send_message(error_response)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down")
        finally:
            self.stop()

    def send_message(self, message: Dict[str, Any]):
        """
        Send a message to stdout.

        Args:
            message: JSON-RPC message to send
        """
        try:
            json_str = json.dumps(message)
            sys.stdout.write(json_str + "\n")
            sys.stdout.flush()
            logger.debug(f"Sent message: {message}")
        except Exception as e:
            logger.error(f"Error sending message: {e}", exc_info=True)

    def stop(self):
        """Stop the transport."""
        self.running = False
        logger.info("MCP server stopped")

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
            message_id: Original message ID (None for parse errors)
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
