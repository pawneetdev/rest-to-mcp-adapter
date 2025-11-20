#!/usr/bin/env python3
"""
Run Binance MCP Server

This script loads a pre-generated Binance registry and starts the MCP server.

Usage:
    1. First generate the registry:
       python generate_binance_registry.py

    2. Then run the server:
       # Method 1: Using environment variables
       export BINANCE_API_KEY="your_api_key"
       export BINANCE_API_SECRET="your_api_secret"
       python run_binance_server.py

       # Method 2: Using config file
       cp binance_config.json.example binance_config.json
       # Edit binance_config.json with your credentials
       python run_binance_server.py

       # Method 3: Public endpoints only (no credentials)
       python run_binance_server.py
"""

import json
import logging
import os
from pathlib import Path

from adapter import (
    MCPServer,
    ToolRegistry,
    APIExecutor,
    NoAuth,
    CanonicalEndpoint,
)
from adapter.mcp import MCPTool

# Import custom Binance auth handler
from binance_auth import BinanceAuth

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_credentials():
    """
    Load Binance credentials from environment variables or config file.

    Priority order:
    1. Environment variables (BINANCE_API_KEY, BINANCE_API_SECRET)
    2. Config file (binance_config.json)
    3. None (for public endpoints only)

    Returns:
        tuple: (api_key, api_secret, base_url) or (None, None, default_base_url)
    """
    # Try environment variables first
    api_key = os.getenv("BINANCE_API_KEY")
    api_secret = os.getenv("BINANCE_API_SECRET")
    base_url = os.getenv("BINANCE_BASE_URL", "https://api.binance.com")

    if api_key and api_secret:
        logger.info("✓ Loaded credentials from environment variables")
        return api_key, api_secret, base_url

    # Try config file
    config_path = Path("binance_config.json")
    if config_path.exists():
        try:
            with open(config_path) as f:
                config = json.load(f)

            api_key = config.get("api_key")
            api_secret = config.get("api_secret")
            base_url = config.get("base_url", "https://api.binance.com")

            if api_key and api_secret:
                logger.info("✓ Loaded credentials from binance_config.json")
                return api_key, api_secret, base_url
            else:
                logger.warning("⚠ binance_config.json exists but missing credentials")
        except json.JSONDecodeError as e:
            logger.error(f"❌ Failed to parse binance_config.json: {e}")
        except Exception as e:
            logger.error(f"❌ Error reading binance_config.json: {e}")

    # No credentials found
    logger.info("⚠ No API credentials found")
    return None, None, base_url


def load_registry_from_file(registry_file: str) -> ToolRegistry:
    """
    Load a pre-generated registry from JSON file.

    Args:
        registry_file: Path to the registry JSON file

    Returns:
        Loaded ToolRegistry
    """
    logger.info(f"Loading registry from {registry_file}...")

    with open(registry_file, 'r') as f:
        data = json.load(f)

    # Create registry
    registry = ToolRegistry(name=data.get('name', 'Binance API'))

    # Load tools
    for tool_data in data.get('tools', []):
        tool = MCPTool(
            name=tool_data['name'],
            description=tool_data['description'],
            inputSchema=tool_data['inputSchema'],
            metadata=tool_data.get('metadata')
        )
        registry.add_tool(tool)

    logger.info(f"✓ Loaded {registry.count()} tools from registry")
    return registry


def load_endpoints_from_file(endpoints_file: str) -> list:
    """
    Load pre-generated endpoints from JSON file.

    Args:
        endpoints_file: Path to the endpoints JSON file

    Returns:
        List of CanonicalEndpoint objects
    """
    logger.info(f"Loading endpoints from {endpoints_file}...")

    with open(endpoints_file, 'r') as f:
        data = json.load(f)

    endpoints = []
    for ep_data in data:
        # Reconstruct CanonicalEndpoint from dict
        endpoint = CanonicalEndpoint(
            name=ep_data['name'],
            path=ep_data['path'],
            method=ep_data['method'],
            operation_id=ep_data.get('operation_id'),
            summary=ep_data.get('summary'),
            description=ep_data.get('description'),
            parameters=ep_data.get('parameters', []),
            request_body=ep_data.get('request_body'),
            responses=ep_data.get('responses', {}),
            tags=ep_data.get('tags', []),
            security=ep_data.get('security', []),
        )
        endpoints.append(endpoint)

    logger.info(f"✓ Loaded {len(endpoints)} endpoints")
    return endpoints


def main():
    """Main function to run the Binance MCP server."""

    # Configuration
    REGISTRY_FILE = "binance_registry.json"
    ENDPOINTS_FILE = "binance_endpoints.json"

    # Load credentials
    api_key, api_secret, BASE_URL = load_credentials()

    # Check if files exist
    if not Path(REGISTRY_FILE).exists():
        logger.error(f"Registry file not found: {REGISTRY_FILE}")
        logger.info("Please run: python generate_binance_registry.py")
        return

    if not Path(ENDPOINTS_FILE).exists():
        logger.error(f"Endpoints file not found: {ENDPOINTS_FILE}")
        logger.info("Please run: python generate_binance_registry.py")
        return

    # Load registry and endpoints
    registry = load_registry_from_file(REGISTRY_FILE)
    endpoints = load_endpoints_from_file(ENDPOINTS_FILE)

    # Create executor with authentication
    if api_key and api_secret:
        auth = BinanceAuth(api_key=api_key, api_secret=api_secret)
        auth_status = "Authenticated (API Key + HMAC SHA256)"
    else:
        logger.info("  Using public endpoints only")
        logger.info("  To enable authenticated endpoints:")
        logger.info("    Option 1: Set environment variables")
        logger.info("      export BINANCE_API_KEY='your_api_key'")
        logger.info("      export BINANCE_API_SECRET='your_api_secret'")
        logger.info("    Option 2: Create binance_config.json from binance_config.json.example")
        auth = NoAuth()
        auth_status = "Public only (no authentication)"

    executor = APIExecutor(
        base_url=BASE_URL,
        auth=auth
    )

    logger.info(f"\nBase URL: {BASE_URL}")
    logger.info(f"Auth: {auth_status}")

    # Create MCP server
    server = MCPServer(
        name="Binance Spot API",
        version="1.0.0",
        tool_registry=registry,
        executor=executor,
        endpoints=endpoints
    )

    logger.info("=" * 70)
    logger.info(f"Starting {server.name} v{server.version}")
    logger.info(f"Tools: {registry.count()}")
    logger.info(f"Endpoints: {len(endpoints)}")
    logger.info("=" * 70)

    # Run the server
    server.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nServer stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
