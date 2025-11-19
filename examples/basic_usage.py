"""
Basic usage examples for the REST → MCP Adapter ingestion pipeline.

This script demonstrates how to use the Phase 1 ingestion layer
to load and normalize API documentation.

Run this example:
    python examples/basic_usage.py
"""

from adapter.pipeline import ingest_api_source
from adapter.parsing import Normalizer


def example_1_ingest_openapi():
    """Example 1: Ingest an OpenAPI specification."""
    print("=" * 60)
    print("Example 1: Ingesting OpenAPI Specification")
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
                  properties:
                    id:
                      type: integer
                    name:
                      type: string
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
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: integer
                  name:
                    type: string
                  email:
                    type: string
"""

    # Ingest the OpenAPI spec
    result = ingest_api_source(
        source="sample_api.yaml",
        raw_content=openapi_yaml,
    )

    print(f"\nIngestion Result: {result}")
    print(f"Format detected: {result.format}")
    print(f"Success: {result.success}")

    if result.success:
        print(f"\nLoaded data type: {type(result.loaded_data)}")
        print(f"API Title: {result.loaded_data.get('info', {}).get('title')}")
        print(f"Paths found: {list(result.loaded_data.get('paths', {}).keys())}")

        # Normalize to canonical format
        normalizer = Normalizer()
        endpoints = normalizer.normalize_openapi(result.loaded_data)

        print(f"\n{len(endpoints)} endpoints normalized:")
        for endpoint in endpoints:
            print(f"  - {endpoint.name}: {endpoint.method} {endpoint.path}")
            print(f"    Parameters: {len(endpoint.parameters)}")
            if endpoint.parameters:
                for param in endpoint.parameters:
                    print(f"      • {param.name} ({param.location}): {param.type}")

    print()


def example_2_ingest_html():
    """Example 2: Ingest HTML documentation."""
    print("=" * 60)
    print("Example 2: Ingesting HTML Documentation")
    print("=" * 60)

    # Sample HTML API documentation
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>API Documentation</title>
    <style>
        body { font-family: Arial; }
        .nav { background: blue; }
    </style>
    <script>
        console.log("This script will be removed");
    </script>
</head>
<body>
    <nav class="nav">Navigation (will be removed)</nav>

    <h1>API Documentation</h1>

    <h2>GET /api/products</h2>
    <p>Retrieve a list of all products.</p>

    <h3>Query Parameters</h3>
    <ul>
        <li><strong>category</strong> (string): Filter by category</li>
        <li><strong>limit</strong> (integer): Maximum number of results</li>
    </ul>

    <h3>Response</h3>
    <pre>
    {
        "products": [
            {"id": 1, "name": "Product A"},
            {"id": 2, "name": "Product B"}
        ]
    }
    </pre>

    <h2>POST /api/orders</h2>
    <p>Create a new order.</p>

    <h3>Request Body</h3>
    <pre>
    {
        "product_id": 123,
        "quantity": 2
    }
    </pre>

    <footer>Copyright 2024 (will be removed)</footer>
</body>
</html>
"""

    # Ingest the HTML documentation
    result = ingest_api_source(
        source="api_docs.html",
        raw_content=html_content,
    )

    print(f"\nIngestion Result: {result}")
    print(f"Format detected: {result.format}")
    print(f"Success: {result.success}")

    if result.success:
        print(f"\nCleaned text preview (first 500 chars):")
        print("-" * 60)
        print(result.loaded_data[:500])
        print("-" * 60)
        print("\nNote: Scripts, styles, and navigation removed.")
        print("This clean text is ready for LLM-based extraction (Phase 2).")

    print()


def example_3_format_detection():
    """Example 3: Automatic format detection."""
    print("=" * 60)
    print("Example 3: Automatic Format Detection")
    print("=" * 60)

    samples = [
        ("OpenAPI JSON", '{"openapi": "3.0.0", "info": {"title": "Test"}}'),
        ("OpenAPI YAML", "openapi: 3.0.0\ninfo:\n  title: Test"),
        ("Swagger 2.0", '{"swagger": "2.0", "info": {"title": "Test"}}'),
        ("HTML", "<html><head><title>API</title></head><body>Docs</body></html>"),
        ("Unknown", "Just some random text"),
    ]

    for label, content in samples:
        result = ingest_api_source(
            source=f"{label}_sample",
            raw_content=content,
        )
        print(f"\n{label}:")
        print(f"  Detected format: {result.format}")
        print(f"  Success: {result.success}")

    print()


def example_4_custom_configuration():
    """Example 4: Using custom configuration."""
    print("=" * 60)
    print("Example 4: Custom Configuration")
    print("=" * 60)

    # Malformed OpenAPI spec (missing required fields)
    malformed_spec = '{"paths": {"/test": {"get": {}}}}'

    # Try with non-strict mode (default)
    print("\nWith non-strict mode (lenient):")
    result = ingest_api_source(
        source="malformed.json",
        raw_content=malformed_spec,
        strict=False,
    )
    print(f"  Success: {result.success}")
    if result.success:
        print(f"  Loaded: {result.loaded_data.keys()}")

    # Try with strict mode
    print("\nWith strict mode:")
    result = ingest_api_source(
        source="malformed.json",
        raw_content=malformed_spec,
        strict=True,
    )
    print(f"  Success: {result.success}")
    if not result.success:
        print(f"  Error: {result.error}")

    print()


def example_5_extending_with_custom_loader():
    """Example 5: Extending with a custom loader (for future formats)."""
    print("=" * 60)
    print("Example 5: Extensibility - Custom Loader Registration")
    print("=" * 60)

    from adapter.ingestion.base_loader import BaseLoader
    from adapter.pipeline.ingestion_pipeline import IngestionPipeline
    from adapter.ingestion.detector import APIFormat

    # Define a custom loader (placeholder for future Postman support)
    class PostmanLoader(BaseLoader):
        """Placeholder loader for Postman collections."""

        def load(self, content: str) -> dict:
            """Load Postman collection (simplified)."""
            import json
            data = json.loads(content)

            # Basic validation
            if "info" not in data or "item" not in data:
                raise ValueError("Invalid Postman collection")

            return data

    # Create pipeline and register custom loader
    pipeline = IngestionPipeline()

    # Note: We can't use APIFormat.POSTMAN yet (not defined),
    # but this shows how you would register custom loaders
    print("\nCustom loader pattern:")
    print("  1. Create a class extending BaseLoader")
    print("  2. Implement the load() method")
    print("  3. Register with pipeline.register_loader()")
    print("\nThis enables easy extension for:")
    print("  - Postman collections")
    print("  - GraphQL schemas")
    print("  - Markdown documentation")
    print("  - PDF documentation")
    print("  - Any custom format")

    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("REST → MCP Adapter - Basic Usage Examples")
    print("Phase 1: Ingestion & Normalization Layer")
    print("=" * 60 + "\n")

    # Run all examples
    example_1_ingest_openapi()
    example_2_ingest_html()
    example_3_format_detection()
    example_4_custom_configuration()
    example_5_extending_with_custom_loader()

    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)
