#!/usr/bin/env python3
"""
Example: Advanced Registry Filtering

This example demonstrates the new limit and pattern matching capabilities
of the ToolRegistry for filtering and selecting tools.
"""

import logging

from adapter import (
    OpenAPILoader,
    Normalizer,
    ToolGenerator,
    ToolRegistry
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_registry():
    """Load OpenAPI spec and create registry with tools."""
    logger.info("Loading OpenAPI spec and generating tools...")

    # Load Petstore API
    loader = OpenAPILoader()
    spec = loader.load("https://petstore3.swagger.io/api/v3/openapi.json")

    # Normalize endpoints
    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)

    # Generate tools
    generator = ToolGenerator(api_name="petstore")
    tools = generator.generate_tools(endpoints)

    # Create registry
    registry = ToolRegistry(name="Petstore API")
    registry.add_tools(tools)

    logger.info(f"✓ Created registry with {registry.count()} tools\n")
    return registry


def example_limit_usage(registry: ToolRegistry):
    """Example: Using limit parameter to get only a subset of tools."""
    logger.info("=" * 70)
    logger.info("Example 1: Using Limit Parameter")
    logger.info("=" * 70)

    # Get all tools
    all_tools = registry.get_all_tools()
    logger.info(f"Total tools: {len(all_tools)}")

    # Get only first 5 tools
    limited_tools = registry.get_all_tools(limit=5)
    logger.info(f"Limited to 5 tools: {len(limited_tools)}")
    for tool in limited_tools:
        logger.info(f"  - {tool.name}")

    # Get first 3 GET endpoints
    logger.info("\nFirst 3 GET endpoints:")
    get_tools = registry.get_tools_by_method("GET", limit=3)
    for tool in get_tools:
        logger.info(f"  - {tool.name}")

    # Get first 5 tools matching 'pet'
    logger.info("\nFirst 5 tools matching 'pet':")
    pet_tools = registry.search_tools("pet", limit=5)
    for tool in pet_tools:
        logger.info(f"  - {tool.name}")


def example_pattern_matching(registry: ToolRegistry):
    """Example: Using regex pattern matching to filter tools."""
    logger.info("\n" + "=" * 70)
    logger.info("Example 2: Pattern Matching")
    logger.info("=" * 70)

    # Pattern 1: Tools with 'pet' or 'pets' in name
    logger.info("\nTools matching pattern 'pets?' (pet or pets):")
    tools = registry.filter_by_pattern(r'pets?', field='name')
    for tool in tools[:5]:  # Show first 5
        logger.info(f"  - {tool.name}")

    # Pattern 2: Tools starting with 'get'
    logger.info("\nTools matching pattern '^.*get.*' (starting with get):")
    tools = registry.filter_by_pattern(r'^[^_]*_get', field='name', limit=5)
    for tool in tools:
        logger.info(f"  - {tool.name}")

    # Pattern 3: Tools with ID in description
    logger.info("\nTools with 'ID' in description (first 3):")
    tools = registry.filter_by_pattern(r'\bid\b', field='description', limit=3)
    for tool in tools:
        logger.info(f"  - {tool.name}: {tool.description[:60]}...")


def example_path_pattern_filtering(registry: ToolRegistry):
    """Example: Filter tools by URL path patterns."""
    logger.info("\n" + "=" * 70)
    logger.info("Example 3: Path Pattern Filtering")
    logger.info("=" * 70)

    # Get tools with path parameters
    logger.info("\nTools with path parameters (e.g., {id}):")
    tools = registry.filter_by_path_pattern(r'\{[^}]+\}', limit=5)
    for tool in tools:
        if tool.metadata and "path" in tool.metadata:
            logger.info(f"  - {tool.name}: {tool.metadata['path']}")

    # Get tools from /pet path
    logger.info("\nTools from /pet path:")
    tools = registry.filter_by_path_pattern(r'^/pet(/|$)', limit=5)
    for tool in tools:
        if tool.metadata and "path" in tool.metadata:
            logger.info(f"  - {tool.name}: {tool.metadata['path']}")

    # Get tools from /store path
    logger.info("\nTools from /store path:")
    tools = registry.filter_by_path_pattern(r'^/store', limit=3)
    for tool in tools:
        if tool.metadata and "path" in tool.metadata:
            logger.info(f"  - {tool.name}: {tool.metadata['path']}")


def example_combined_filtering(registry: ToolRegistry):
    """Example: Combine multiple filters with get_tools()."""
    logger.info("\n" + "=" * 70)
    logger.info("Example 4: Combined Filtering")
    logger.info("=" * 70)

    # Get first 5 GET endpoints with 'pet' in name
    logger.info("\nGET endpoints with 'pet' in name (limit 5):")
    tools = registry.get_tools(
        method="GET",
        pattern=r'pet',
        pattern_field='name',
        limit=5
    )
    for tool in tools:
        logger.info(f"  - {tool.name} [{tool.metadata.get('method')}]")

    # Get POST endpoints with path pattern
    logger.info("\nPOST endpoints from /pet path:")
    tools = registry.get_tools(
        method="POST",
        pattern=r'^/pet',
        pattern_field='path',
        limit=3
    )
    for tool in tools:
        if tool.metadata and "path" in tool.metadata:
            logger.info(f"  - {tool.name}: {tool.metadata['path']}")

    # Get DELETE endpoints with 'id' in path
    logger.info("\nDELETE endpoints with path parameters:")
    tools = registry.get_tools(
        method="DELETE",
        pattern=r'\{[^}]+\}',
        pattern_field='path',
        limit=3
    )
    for tool in tools:
        if tool.metadata and "path" in tool.metadata:
            logger.info(f"  - {tool.name}: {tool.metadata['path']}")


def example_practical_use_cases(registry: ToolRegistry):
    """Example: Practical use cases for filtering."""
    logger.info("\n" + "=" * 70)
    logger.info("Example 5: Practical Use Cases")
    logger.info("=" * 70)

    # Use case 1: Get all read-only (GET) endpoints for documentation
    logger.info("\nUse case 1: Get read-only endpoints (first 10):")
    tools = registry.get_tools(method="GET", limit=10)
    logger.info(f"  Found {len(tools)} GET endpoints")

    # Use case 2: Get all endpoints that modify data
    logger.info("\nUse case 2: Get data-modifying endpoints:")
    post_tools = registry.get_tools(method="POST", limit=5)
    put_tools = registry.get_tools(method="PUT", limit=5)
    delete_tools = registry.get_tools(method="DELETE", limit=5)
    logger.info(f"  POST: {len(post_tools)}")
    logger.info(f"  PUT: {len(put_tools)}")
    logger.info(f"  DELETE: {len(delete_tools)}")

    # Use case 3: Get only endpoints for a specific resource
    logger.info("\nUse case 3: Get all 'pet' resource endpoints (first 10):")
    tools = registry.filter_by_pattern(r'_pet(_|$)', field='name', limit=10)
    for tool in tools:
        method = tool.metadata.get('method', 'UNKNOWN') if tool.metadata else 'UNKNOWN'
        logger.info(f"  - {tool.name} [{method}]")

    # Use case 4: Export limited set for testing
    logger.info("\nUse case 4: Export first 5 tools for testing:")
    limited_tools = registry.get_all_tools(limit=5)

    # Create a new registry with limited tools
    test_registry = ToolRegistry(name="Test Subset")
    test_registry.add_tools(limited_tools)
    test_registry.export_json("/tmp/test_tools.json")
    logger.info(f"  ✓ Exported {test_registry.count()} tools to /tmp/test_tools.json")

    # Use case 5: Find endpoints with specific patterns for monitoring
    logger.info("\nUse case 5: Find endpoints with numeric IDs in path:")
    tools = registry.filter_by_path_pattern(r'/\{[^}]*[Ii][Dd][^}]*\}', limit=10)
    for tool in tools:
        if tool.metadata and "path" in tool.metadata:
            logger.info(f"  - {tool.name}: {tool.metadata['path']}")


def main():
    """Run all filtering examples."""
    # Set up registry
    registry = setup_registry()

    # Run examples
    example_limit_usage(registry)
    example_pattern_matching(registry)
    example_path_pattern_filtering(registry)
    example_combined_filtering(registry)
    example_practical_use_cases(registry)

    logger.info("\n" + "=" * 70)
    logger.info("All examples completed!")
    logger.info("=" * 70)
    logger.info("\nNew Registry Features:")
    logger.info("✓ limit parameter on all filter methods")
    logger.info("✓ filter_by_pattern() - regex filtering on name/description/path")
    logger.info("✓ filter_by_path_pattern() - convenience method for path filtering")
    logger.info("✓ get_tools() - combined filtering with method, tag, pattern, and limit")
    logger.info("\nSee LIBRARY_USAGE.md for more details")


if __name__ == "__main__":
    main()
