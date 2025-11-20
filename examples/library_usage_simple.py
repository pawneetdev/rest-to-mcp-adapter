#!/usr/bin/env python3
"""
Simple example: Using rest-to-mcp-adapter as a library

This shows the most common use case: creating an MCP server from an OpenAPI spec.
"""

import logging
import sys

# Import from the adapter library
from adapter import (
    OpenAPILoader,
    Normalizer,
    ToolGenerator,
    ToolRegistry,
    APIExecutor,
    BearerAuth,
    NoAuth,
    MCPServer
)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # MCP uses stdout for protocol, stderr for logs
)

logger = logging.getLogger(__name__)


def create_mcp_server(
    openapi_url: str,
    base_url: str,
    api_name: str,
    server_name: str,
    auth_token: str = None,
):
    """
    Create an MCP server from an OpenAPI specification.

    Args:
        openapi_url: URL or path to OpenAPI spec
        base_url: Base URL for API calls
        api_name: Name prefix for tools
        server_name: Display name for the MCP server
        auth_token: Optional bearer token for authentication

    Returns:
        MCPServer instance ready to run
    """
    logger.info(f"Creating MCP server from {openapi_url}")

    # Phase 1: Load and normalize OpenAPI spec
    logger.info("Phase 1: Loading OpenAPI specification...")
    loader = OpenAPILoader()
    spec = loader.load(openapi_url)

    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)
    logger.info(f"✓ Loaded {len(endpoints)} endpoints")

    # Phase 2: Generate MCP tools
    logger.info("Phase 2: Generating MCP tools...")
    generator = ToolGenerator(api_name=api_name)
    tools = generator.generate_tools(endpoints)

    registry = ToolRegistry(name=f"{api_name} API")
    registry.add_tools(tools)
    logger.info(f"✓ Generated {len(tools)} MCP tools")

    # Phase 3: Create API executor with authentication
    logger.info("Phase 3: Setting up API executor...")
    if auth_token:
        auth = BearerAuth(token=auth_token)
        logger.info("✓ Using Bearer token authentication")
    else:
        auth = NoAuth()
        logger.info("✓ No authentication")

    executor = APIExecutor(
        base_url=base_url,
        auth=auth,
        max_retries=3,
        retry_backoff=1.0,
        timeout=30
    )

    # Phase 4: Create MCP server
    logger.info("Phase 4: Creating MCP server...")
    server = MCPServer(
        name=server_name,
        version="1.0.0",
        tool_registry=registry,
        executor=executor,
        endpoints=endpoints
    )

    logger.info("=" * 70)
    logger.info(f"MCP Server Ready: {server_name}")
    logger.info(f"  Tools: {registry.count()}")
    logger.info(f"  Base URL: {base_url}")
    logger.info(f"  Authentication: {auth}")
    logger.info("=" * 70)

    return server


def main():
    """
    Example: Create an MCP server for the Petstore API
    """
    # Configuration
    OPENAPI_URL = "https://petstore3.swagger.io/api/v3/openapi.json"
    BASE_URL = "https://petstore3.swagger.io/api/v3"
    API_NAME = "petstore"
    SERVER_NAME = "Petstore MCP Server"
    AUTH_TOKEN = None  # Petstore is public, no auth needed

    # Create and run the server
    server = create_mcp_server(
        openapi_url=OPENAPI_URL,
        base_url=BASE_URL,
        api_name=API_NAME,
        server_name=SERVER_NAME,
        auth_token=AUTH_TOKEN
    )

    # Start the server (blocks until stopped)
    logger.info("Starting MCP server on stdio transport...")
    server.run()


if __name__ == "__main__":
    main()
