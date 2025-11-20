#!/usr/bin/env python3
"""
Simple Binance MCP Server - Regenerates tools on startup

This script loads the Binance OpenAPI spec and starts the MCP server.
No pre-generated files needed.

Usage:
    # For public endpoints only (no authentication)
    python run_binance_simple.py

    # For authenticated endpoints (set environment variables)
    export BINANCE_API_KEY="your_api_key"
    export BINANCE_API_SECRET="your_api_secret"
    python run_binance_simple.py
"""

import logging
import os

from adapter import (
    OpenAPILoader,
    Normalizer,
    ToolGenerator,
    ToolRegistry,
    MCPServer,
    APIExecutor,
    NoAuth,
)

# Import custom Binance auth handler
from binance_auth import BinanceAuth

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to run the Binance MCP server."""

    # Configuration
    OPENAPI_URL = "https://raw.githubusercontent.com/binance/binance-api-swagger/refs/heads/master/spot_api.yaml"
    BASE_URL = "https://api.binance.com"
    API_NAME = "binance"

    logger.info("=" * 70)
    logger.info("Binance Spot API MCP Server")
    logger.info("=" * 70)

    # Load OpenAPI spec
    logger.info("Loading Binance OpenAPI specification...")
    loader = OpenAPILoader()
    spec = loader.load(OPENAPI_URL)
    logger.info("✓ OpenAPI spec loaded")

    # Normalize endpoints
    logger.info("Normalizing endpoints...")
    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)
    logger.info(f"✓ Normalized {len(endpoints)} endpoints")

    # Generate tools
    logger.info("Generating MCP tools...")
    generator = ToolGenerator(api_name=API_NAME)
    tools = generator.generate_tools(endpoints)
    logger.info(f"✓ Generated {len(tools)} tools")

    # Create registry
    logger.info("Creating tool registry...")
    registry = ToolRegistry(name="Binance Spot API")
    registry.add_tools(tools)
    logger.info(f"✓ Registry created with {registry.count()} tools")

    # Tool distribution
    methods = {}
    for tool in tools:
        method = tool.metadata.get('method', 'UNKNOWN')
        methods[method] = methods.get(method, 0) + 1

    logger.info("\nTool distribution by HTTP method:")
    for method, count in sorted(methods.items()):
        logger.info(f"  {method}: {count}")

    # Create executor with authentication
    # Check for API credentials in environment variables
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")

    if api_key and api_secret:
        logger.info("✓ Found Binance API credentials in environment")
        auth = BinanceAuth(api_key=api_key, api_secret=api_secret)
        auth_status = "Authenticated (API Key + HMAC SHA256)"
    else:
        logger.info("⚠ No API credentials found - using public endpoints only")
        logger.info("  To enable authenticated endpoints, set:")
        logger.info("    export BINANCE_API_KEY='your_api_key'")
        logger.info("    export BINANCE_API_SECRET='your_api_secret'")
        auth = NoAuth()
        auth_status = "Public only (no authentication)"

    executor = APIExecutor(
        base_url=BASE_URL,
        auth=auth
    )

    logger.info(f"\nBase URL: {BASE_URL}")
    logger.info(f"Auth: {auth_status}\n")

    # Create MCP server
    server = MCPServer(
        name="Binance Spot API",
        version="1.0.0",
        tool_registry=registry,
        executor=executor,
        endpoints=endpoints
    )

    logger.info("=" * 70)
    logger.info("Starting MCP server...")
    logger.info(f"Server: {server.name} v{server.version}")
    logger.info(f"Tools: {registry.count()}")
    logger.info("=" * 70)
    logger.info("")

    # Run the server
    server.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nServer stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
