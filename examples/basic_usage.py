"""
Basic usage examples for the REST → MCP Adapter ingestion layer.

This script demonstrates how to use the Phase 1 ingestion layer
to load and normalize API documentation from various sources.

Run this example:
    python examples/basic_usage.py
"""

from adapter.ingestion import OpenAPILoader
from adapter.parsing import Normalizer


def example_1_openapi_from_raw_content():
    """Example 1: Load OpenAPI from raw YAML content."""
    print("=" * 60)
    print("Example 1: OpenAPI from Raw YAML Content")
    print("=" * 60)

    # Sample OpenAPI spec (minimal example)
    openapi_yaml = """
openapi: 3.0.0
info:
  title: Sample API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List all users
      operationId: listUsers
      tags:
        - users
      parameters:
        - name: limit
          in: query
          description: How many items to return
          required: false
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: Array of users
          content:
            application/json:
              schema:
                type: array
                items:
                  type: object
  /users/{userId}:
    get:
      summary: Get a user by ID
      operationId: getUserById
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: User object
"""

    # Load the OpenAPI spec
    loader = OpenAPILoader()
    spec_dict = loader.load(openapi_yaml)

    print(f"\nLoaded OpenAPI specification")
    print(f"API Title: {spec_dict.get('info', {}).get('title')}")
    print(f"Paths found: {list(spec_dict.get('paths', {}).keys())}")

    # Normalize to canonical format
    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec_dict)

    print(f"\n{len(endpoints)} endpoints normalized:")
    for endpoint in endpoints:
        print(f"  - {endpoint.name}: {endpoint.method} {endpoint.path}")
        if endpoint.parameters:
            print(f"    Parameters: {len(endpoint.parameters)}")
            for param in endpoint.parameters[:2]:  # Show first 2
                print(f"      • {param.name} ({param.location}): {param.type}")

    print()


def example_2_openapi_from_url():
    """Example 2: Load OpenAPI from a URL (if available)."""
    print("=" * 60)
    print("Example 2: OpenAPI from URL")
    print("=" * 60)

    # Example using a public OpenAPI spec URL
    # Note: This requires internet connection
    url = "https://petstore3.swagger.io/api/v3/openapi.json"

    print(f"\nAttempting to load from: {url}")
    print("(Requires internet connection)")

    try:
        loader = OpenAPILoader()
        spec_dict = loader.load_from_url(url)

        print(f"✓ Successfully loaded!")
        print(f"API Title: {spec_dict.get('info', {}).get('title')}")
        print(f"API Version: {spec_dict.get('info', {}).get('version')}")
        print(f"Number of paths: {len(spec_dict.get('paths', {}))}")

    except Exception as e:
        print(f"✗ Failed to load (this is okay for the demo): {e}")

    print()


def example_3_openapi_from_file():
    """Example 3: Load OpenAPI from a file path."""
    print("=" * 60)
    print("Example 3: OpenAPI from File Path")
    print("=" * 60)

    # This demonstrates the API for file loading
    # In a real scenario, you'd have an actual file

    print("\nFile loading API:")
    print("  loader = OpenAPILoader()")
    print("  spec = loader.load_from_file('./specs/api.yaml')")
    print("  # or")
    print("  spec = loader.load('./specs/api.yaml')")  # Auto-detects file
    print("\nThe loader automatically detects URLs, file paths, or raw content!")

    print()


def example_4_convenience_functions():
    """Example 4: Using convenience functions."""
    print("=" * 60)
    print("Example 4: Convenience Functions (Quick Prototyping)")
    print("=" * 60)

    from adapter.pipeline import load_openapi

    print("\nFor quick prototyping, use convenience functions:")
    print()
    print("  from adapter.pipeline import load_openapi")
    print()
    print("  # Load OpenAPI")
    print("  spec = load_openapi('https://api.example.com/openapi.json')")
    print("  spec = load_openapi('./specs/api.yaml')")
    print("  spec = load_openapi(raw_yaml_content)")
    print()
    print("For production code, use the loader classes directly:")
    print("  from adapter.ingestion import OpenAPILoader")

    print()


def example_5_normalize_to_canonical():
    """Example 5: Complete workflow - Load & Normalize."""
    print("=" * 60)
    print("Example 5: Complete Workflow (Load + Normalize)")
    print("=" * 60)

    openapi_spec = """
openapi: 3.0.0
info:
  title: E-Commerce API
  version: 2.0.0
paths:
  /products/{productId}:
    get:
      operationId: getProductById
      summary: Get product details
      parameters:
        - name: productId
          in: path
          required: true
          schema:
            type: string
        - name: includeReviews
          in: query
          required: false
          schema:
            type: boolean
      responses:
        '200':
          description: Product details
"""

    # Step 1: Load OpenAPI spec
    loader = OpenAPILoader()
    spec_dict = loader.load(openapi_spec)

    # Step 2: Normalize to canonical format
    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec_dict)

    # Step 3: Use canonical endpoints
    print(f"\nProcessed {len(endpoints)} endpoint(s):\n")
    for endpoint in endpoints:
        print(f"Endpoint: {endpoint.name}")
        print(f"  Method: {endpoint.method}")
        print(f"  Path: {endpoint.path}")
        print(f"  Description: {endpoint.summary}")
        print(f"  Parameters:")
        for param in endpoint.parameters:
            req = "required" if param.required else "optional"
            print(f"    - {param.name} ({param.location}, {param.type}, {req})")

    print("\nNext steps:")
    print("  → Phase 2: Generate MCP tool definitions from canonical endpoints")
    print("  → Phase 3: Build runtime REST execution engine")
    print("  → Phase 4: Deploy agent-facing MCP server")

    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("REST → MCP Adapter - Basic Usage Examples")
    print("Phase 1: Ingestion & Normalization Layer")
    print("=" * 60 + "\n")

    # Run all examples
    example_1_openapi_from_raw_content()
    example_2_openapi_from_url()
    example_3_openapi_from_file()
    example_4_convenience_functions()
    example_5_normalize_to_canonical()

    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)
