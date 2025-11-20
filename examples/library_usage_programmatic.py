#!/usr/bin/env python3
"""
Programmatic API usage example

This shows how to use the adapter library to make API calls directly
without running an MCP server.
"""

import logging

from adapter import (
    OpenAPILoader,
    Normalizer,
    APIExecutor,
    NoAuth,
    ToolGenerator,
    ToolRegistry
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_direct_api_calls():
    """
    Example: Make direct API calls without running an MCP server
    """
    logger.info("=" * 70)
    logger.info("Example: Direct API Calls")
    logger.info("=" * 70)

    # Load OpenAPI spec
    loader = OpenAPILoader()
    spec = loader.load("https://petstore3.swagger.io/api/v3/openapi.json")

    # Normalize endpoints
    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)
    logger.info(f"Loaded {len(endpoints)} endpoints")

    # Create API executor
    executor = APIExecutor(
        base_url="https://petstore3.swagger.io/api/v3",
        auth=NoAuth(),
        max_retries=3
    )

    # Find a specific endpoint
    get_inventory_endpoint = None
    for ep in endpoints:
        if "inventory" in ep.name and ep.method == "GET":
            get_inventory_endpoint = ep
            break

    if get_inventory_endpoint:
        logger.info(f"\nExecuting endpoint: {get_inventory_endpoint.name}")
        logger.info(f"  Method: {get_inventory_endpoint.method}")
        logger.info(f"  Path: {get_inventory_endpoint.path}")

        # Execute the API call
        result = executor.execute(
            endpoint=get_inventory_endpoint,
            parameters={}
        )

        # Handle the response
        if result.success:
            logger.info("\n✓ API call succeeded!")
            logger.info(f"  Status Code: {result.response.status_code}")
            logger.info(f"  Execution Time: {result.execution_time_ms:.2f}ms")
            logger.info(f"  Response Data: {result.response.data}")
        else:
            logger.error("\n✗ API call failed!")
            logger.error(f"  Error: {result.response.error}")
            logger.error(f"  Status Code: {result.response.status_code}")


def example_tool_generation():
    """
    Example: Generate and export MCP tools without running a server
    """
    logger.info("\n" + "=" * 70)
    logger.info("Example: Tool Generation and Export")
    logger.info("=" * 70)

    # Load and normalize
    loader = OpenAPILoader()
    spec = loader.load("https://petstore3.swagger.io/api/v3/openapi.json")
    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)

    # Generate tools
    generator = ToolGenerator(api_name="petstore")
    tools = generator.generate_tools(endpoints)
    logger.info(f"Generated {len(tools)} MCP tools")

    # Create registry
    registry = ToolRegistry(name="Petstore API")
    registry.add_tools(tools)

    # Search for specific tools
    logger.info("\nSearching for 'pet' related tools:")
    pet_tools = registry.search_tools("pet")
    for tool in pet_tools[:5]:  # Show first 5
        logger.info(f"  - {tool.name}: {tool.description[:60]}...")

    # Filter by HTTP method
    logger.info("\nGET endpoints:")
    get_tools = registry.get_tools_by_method("GET")
    logger.info(f"  Found {len(get_tools)} GET endpoints")

    # Export to JSON
    output_file = "/tmp/petstore_tools.json"
    registry.export_json(output_file)
    logger.info(f"\n✓ Exported tools to {output_file}")


def example_batch_calls():
    """
    Example: Execute multiple API calls in batch
    """
    logger.info("\n" + "=" * 70)
    logger.info("Example: Batch API Calls")
    logger.info("=" * 70)

    # Load and normalize
    loader = OpenAPILoader()
    spec = loader.load("https://petstore3.swagger.io/api/v3/openapi.json")
    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)

    # Create executor
    executor = APIExecutor(
        base_url="https://petstore3.swagger.io/api/v3",
        auth=NoAuth()
    )

    # Prepare batch calls
    batch_calls = []

    # Find GET endpoints to call
    for ep in endpoints:
        if ep.method == "GET" and not ep.parameters:  # No required params
            batch_calls.append((ep, {}))
            if len(batch_calls) >= 3:  # Limit to 3 for demo
                break

    # Execute batch
    logger.info(f"\nExecuting {len(batch_calls)} API calls...")
    results = executor.execute_batch(batch_calls)

    # Display results
    for result in results:
        status = "✓" if result.success else "✗"
        logger.info(f"{status} {result.endpoint_name}: {result.execution_time_ms:.0f}ms")


def example_custom_authentication():
    """
    Example: Using different authentication methods
    """
    from adapter import APIKeyAuth, BasicAuth, BearerAuth

    logger.info("\n" + "=" * 70)
    logger.info("Example: Authentication Methods")
    logger.info("=" * 70)

    # Example 1: API Key in header
    logger.info("\n1. API Key in Header:")
    auth1 = APIKeyAuth(
        key="your-api-key",
        location="header",
        name="X-API-Key"
    )
    logger.info(f"   {auth1}")

    # Example 2: API Key in query parameter
    logger.info("\n2. API Key in Query Parameter:")
    auth2 = APIKeyAuth(
        key="your-api-key",
        location="query",
        name="api_key"
    )
    logger.info(f"   {auth2}")

    # Example 3: Basic Authentication
    logger.info("\n3. Basic Authentication:")
    auth3 = BasicAuth(
        username="user",
        password="pass"
    )
    logger.info(f"   {auth3}")

    # Example 4: Bearer Token
    logger.info("\n4. Bearer Token:")
    auth4 = BearerAuth(token="your-token")
    logger.info(f"   {auth4}")

    # You can use any of these with APIExecutor
    executor = APIExecutor(
        base_url="https://api.example.com",
        auth=auth1  # Choose your auth method
    )
    logger.info(f"\n✓ Executor created with {executor.auth}")


def main():
    """
    Run all examples
    """
    # Example 1: Direct API calls
    example_direct_api_calls()

    # Example 2: Tool generation and export
    example_tool_generation()

    # Example 3: Batch API calls
    example_batch_calls()

    # Example 4: Authentication methods
    example_custom_authentication()

    logger.info("\n" + "=" * 70)
    logger.info("All examples completed!")
    logger.info("=" * 70)


if __name__ == "__main__":
    main()
