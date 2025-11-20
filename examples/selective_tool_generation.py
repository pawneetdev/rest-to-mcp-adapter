#!/usr/bin/env python3
"""
Example: Selective Tool Generation

This example demonstrates how to selectively generate tools using
filters during the generation phase (not just filtering after).
"""

import logging

from adapter import (
    OpenAPILoader,
    Normalizer,
    ToolGenerator,
    ToolRegistry,
    APIExecutor,
    NoAuth,
    MCPServer
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_limiting():
    """Example: Generate only a limited number of tools."""
    logger.info("=" * 70)
    logger.info("Example 1: Basic Limiting")
    logger.info("=" * 70)

    # Load OpenAPI spec
    loader = OpenAPILoader()
    spec = loader.load("https://petstore3.swagger.io/api/v3/openapi.json")

    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)
    logger.info(f"Total endpoints available: {len(endpoints)}")

    # Generate only first 5 tools
    generator = ToolGenerator(api_name="petstore")
    tools = generator.generate_tools(endpoints, limit=5)

    logger.info(f"Generated {len(tools)} tools (limited to 5)")
    for tool in tools:
        logger.info(f"  - {tool.name}")


def example_method_filtering():
    """Example: Generate tools only for specific HTTP methods."""
    logger.info("\n" + "=" * 70)
    logger.info("Example 2: Method Filtering")
    logger.info("=" * 70)

    loader = OpenAPILoader()
    spec = loader.load("https://petstore3.swagger.io/api/v3/openapi.json")
    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)

    # Generate only GET endpoints
    generator = ToolGenerator(api_name="petstore")
    get_tools = generator.generate_tools(
        endpoints,
        method_filter='GET'
    )
    logger.info(f"GET tools: {len(get_tools)}")

    # Generate only POST endpoints
    post_tools = generator.generate_tools(
        endpoints,
        method_filter='POST'
    )
    logger.info(f"POST tools: {len(post_tools)}")

    # Generate only DELETE endpoints (limited to 3)
    delete_tools = generator.generate_tools(
        endpoints,
        method_filter='DELETE',
        limit=3
    )
    logger.info(f"DELETE tools (limited to 3): {len(delete_tools)}")
    for tool in delete_tools:
        logger.info(f"  - {tool.name}")


def example_path_pattern():
    """Example: Generate tools matching specific path patterns."""
    logger.info("\n" + "=" * 70)
    logger.info("Example 3: Path Pattern Filtering")
    logger.info("=" * 70)

    loader = OpenAPILoader()
    spec = loader.load("https://petstore3.swagger.io/api/v3/openapi.json")
    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)

    generator = ToolGenerator(api_name="petstore")

    # Generate tools for /pet paths only
    logger.info("\nTools for /pet paths:")
    pet_tools = generator.generate_tools(
        endpoints,
        path_pattern=r'^/pet'
    )
    logger.info(f"Found {len(pet_tools)} pet-related tools")
    for tool in pet_tools[:5]:  # Show first 5
        if tool.metadata and "path" in tool.metadata:
            logger.info(f"  - {tool.name}: {tool.metadata['path']}")

    # Generate tools for /store paths only
    logger.info("\nTools for /store paths:")
    store_tools = generator.generate_tools(
        endpoints,
        path_pattern=r'^/store'
    )
    logger.info(f"Found {len(store_tools)} store-related tools")
    for tool in store_tools:
        if tool.metadata and "path" in tool.metadata:
            logger.info(f"  - {tool.name}: {tool.metadata['path']}")

    # Generate tools with path parameters
    logger.info("\nTools with path parameters (limit 5):")
    param_tools = generator.generate_tools(
        endpoints,
        path_pattern=r'\{[^}]+\}',
        limit=5
    )
    for tool in param_tools:
        if tool.metadata and "path" in tool.metadata:
            logger.info(f"  - {tool.name}: {tool.metadata['path']}")


def example_combined_filters():
    """Example: Combine multiple filters for precise tool selection."""
    logger.info("\n" + "=" * 70)
    logger.info("Example 4: Combined Filters")
    logger.info("=" * 70)

    loader = OpenAPILoader()
    spec = loader.load("https://petstore3.swagger.io/api/v3/openapi.json")
    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)

    generator = ToolGenerator(api_name="petstore")

    # Get only GET endpoints from /pet path, limited to 3
    logger.info("\nGET endpoints from /pet path (first 3):")
    tools = generator.generate_tools(
        endpoints,
        method_filter='GET',
        path_pattern=r'^/pet',
        limit=3
    )
    for tool in tools:
        method = tool.metadata.get('method', '') if tool.metadata else ''
        path = tool.metadata.get('path', '') if tool.metadata else ''
        logger.info(f"  - {tool.name} [{method}] {path}")

    # Get POST endpoints with path parameters
    logger.info("\nPOST endpoints with path parameters:")
    tools = generator.generate_tools(
        endpoints,
        method_filter='POST',
        path_pattern=r'\{[^}]+\}'
    )
    for tool in tools:
        method = tool.metadata.get('method', '') if tool.metadata else ''
        path = tool.metadata.get('path', '') if tool.metadata else ''
        logger.info(f"  - {tool.name} [{method}] {path}")


def example_create_specialized_server():
    """Example: Create an MCP server with only specific tools."""
    logger.info("\n" + "=" * 70)
    logger.info("Example 5: Creating Specialized MCP Server")
    logger.info("=" * 70)

    loader = OpenAPILoader()
    spec = loader.load("https://petstore3.swagger.io/api/v3/openapi.json")
    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)

    # Scenario: Create a read-only server (GET endpoints only)
    logger.info("\nCreating read-only MCP server (GET endpoints only)...")

    generator = ToolGenerator(api_name="petstore")
    readonly_tools = generator.generate_tools(
        endpoints,
        method_filter='GET'
    )

    # Create registry with read-only tools
    registry = ToolRegistry(name="Petstore Read-Only API")
    registry.add_tools(readonly_tools)

    logger.info(f"✓ Registry created with {registry.count()} read-only tools")

    # Filter endpoints to match tools (GET only)
    readonly_endpoints = [ep for ep in endpoints if ep.method == 'GET']

    # Create executor (no auth for petstore)
    executor = APIExecutor(
        base_url="https://petstore3.swagger.io/api/v3",
        auth=NoAuth()
    )

    # Create MCP server
    server = MCPServer(
        name="Petstore Read-Only Server",
        version="1.0.0",
        tool_registry=registry,
        executor=executor,
        endpoints=readonly_endpoints
    )

    logger.info("✓ Read-only MCP server created")
    logger.info(f"  Server: {server.name}")
    logger.info(f"  Tools: {registry.count()}")
    logger.info(f"  All tools are GET (read-only)")
    logger.info("\nTo run this server: server.run()")


def example_practical_use_cases():
    """Example: Practical scenarios for selective tool generation."""
    logger.info("\n" + "=" * 70)
    logger.info("Example 6: Practical Use Cases")
    logger.info("=" * 70)

    loader = OpenAPILoader()
    spec = loader.load("https://petstore3.swagger.io/api/v3/openapi.json")
    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)
    generator = ToolGenerator(api_name="petstore")

    # Use case 1: Testing/Development - Only first 5 tools
    logger.info("\nUse case 1: Generate minimal set for testing (5 tools):")
    test_tools = generator.generate_tools(endpoints, limit=5)
    logger.info(f"  Generated {len(test_tools)} tools for testing")

    # Use case 2: Public API - Only read operations
    logger.info("\nUse case 2: Public API with read-only access:")
    public_tools = generator.generate_tools(
        endpoints,
        method_filter='GET'
    )
    logger.info(f"  Generated {len(public_tools)} GET tools")

    # Use case 3: Admin panel - Only write operations
    logger.info("\nUse case 3: Admin panel with write operations:")
    post_tools = generator.generate_tools(
        endpoints,
        method_filter='POST'
    )
    put_tools = generator.generate_tools(
        endpoints,
        method_filter='PUT'
    )
    delete_tools = generator.generate_tools(
        endpoints,
        method_filter='DELETE'
    )
    admin_tools_count = len(post_tools) + len(put_tools) + len(delete_tools)
    logger.info(f"  Generated {admin_tools_count} write operation tools")
    logger.info(f"    POST: {len(post_tools)}")
    logger.info(f"    PUT: {len(put_tools)}")
    logger.info(f"    DELETE: {len(delete_tools)}")

    # Use case 4: Resource-specific API - Only /pet endpoints
    logger.info("\nUse case 4: Pet-specific API:")
    pet_tools = generator.generate_tools(
        endpoints,
        path_pattern=r'^/pet'
    )
    logger.info(f"  Generated {len(pet_tools)} pet-specific tools")

    # Use case 5: Large API subset - Get first 100 from large API
    logger.info("\nUse case 5: Subset of large API (first 10 for demo):")
    subset_tools = generator.generate_tools(endpoints, limit=10)
    logger.info(f"  Generated {len(subset_tools)} tools from total {len(endpoints)}")


def main():
    """Run all examples."""
    example_basic_limiting()
    example_method_filtering()
    example_path_pattern()
    example_combined_filters()
    example_create_specialized_server()
    example_practical_use_cases()

    logger.info("\n" + "=" * 70)
    logger.info("All examples completed!")
    logger.info("=" * 70)
    logger.info("\nToolGenerator Filtering Features:")
    logger.info("✓ limit - Generate only N tools")
    logger.info("✓ method_filter - Filter by HTTP method (GET, POST, etc.)")
    logger.info("✓ path_pattern - Regex filter for URL paths")
    logger.info("✓ Combine all filters for precise control")
    logger.info("\nBenefits:")
    logger.info("• Faster tool generation (skip unwanted tools)")
    logger.info("• Reduced memory usage (fewer tools to process)")
    logger.info("• Specialized servers (read-only, admin, resource-specific)")
    logger.info("• Testing/development (minimal tool sets)")


if __name__ == "__main__":
    main()
