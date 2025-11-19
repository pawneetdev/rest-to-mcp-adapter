"""
Phase 2 usage examples: MCP Tool Generation

This script demonstrates how to convert REST API endpoints into
MCP-compatible tool definitions.

Run this example:
    python examples/phase2_mcp_tools.py
"""

from adapter.ingestion import OpenAPILoader
from adapter.parsing import Normalizer
from adapter.mcp import ToolGenerator, ToolRegistry


def example_1_basic_tool_generation():
    """Example 1: Basic MCP tool generation from OpenAPI."""
    print("=" * 60)
    print("Example 1: Basic MCP Tool Generation")
    print("=" * 60)

    # Sample OpenAPI spec
    openapi_yaml = """
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
paths:
  /users/{userId}:
    get:
      summary: Get user by ID
      operationId: getUserById
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
          description: Unique user identifier
        - name: include_details
          in: query
          required: false
          schema:
            type: boolean
            default: false
          description: Include detailed user information
      responses:
        '200':
          description: User object
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: string
                  name:
                    type: string
                  email:
                    type: string
"""

    # Step 1: Load and normalize OpenAPI spec
    loader = OpenAPILoader()
    spec = loader.load(openapi_yaml)

    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)

    print(f"\nNormalized {len(endpoints)} endpoint(s)")

    # Step 2: Generate MCP tools
    generator = ToolGenerator()
    tools = generator.generate_tools(endpoints)

    print(f"Generated {len(tools)} MCP tool(s)\n")

    # Step 3: Display tool details
    for tool in tools:
        print(f"Tool: {tool.name}")
        print(f"Description: {tool.description[:100]}...")
        print(f"Input Schema:")
        print(f"  Properties: {list(tool.inputSchema.get('properties', {}).keys())}")
        print(f"  Required: {tool.inputSchema.get('required', [])}")
        if tool.metadata:
            print(f"Metadata:")
            print(f"  Method: {tool.metadata.get('method')}")
            print(f"  Path: {tool.metadata.get('path')}")

    print()


def example_2_tool_registry():
    """Example 2: Using the ToolRegistry to manage tools."""
    print("=" * 60)
    print("Example 2: Tool Registry Management")
    print("=" * 60)

    # Generate sample tools
    openapi_yaml = """
openapi: 3.0.0
info:
  title: E-Commerce API
  version: 1.0.0
paths:
  /products:
    get:
      summary: List products
      operationId: listProducts
      tags:
        - products
      parameters:
        - name: category
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Product list
  /orders:
    post:
      summary: Create order
      operationId: createOrder
      tags:
        - orders
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                product_id:
                  type: string
                quantity:
                  type: integer
              required:
                - product_id
      responses:
        '201':
          description: Order created
"""

    loader = OpenAPILoader()
    spec = loader.load(openapi_yaml)

    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)

    generator = ToolGenerator(api_name="ecommerce")
    tools = generator.generate_tools(endpoints)

    # Create registry
    registry = ToolRegistry(name="E-Commerce API Tools")
    registry.add_tools(tools)

    print(f"\nRegistry: {registry}")
    print(f"Total tools: {registry.count()}")
    print(f"Tool names: {registry.get_tool_names()}")

    # Filter by tags
    print(f"\nAll tags: {registry.get_all_tags()}")
    product_tools = registry.get_tools_by_tag("products")
    print(f"Product tools: {[t.name for t in product_tools]}")

    # Filter by method
    post_tools = registry.get_tools_by_method("POST")
    print(f"POST tools: {[t.name for t in post_tools]}")

    # Search
    order_tools = registry.search_tools("order")
    print(f"Tools matching 'order': {[t.name for t in order_tools]}")

    print()


def example_3_export_to_json():
    """Example 3: Export tools to JSON format."""
    print("=" * 60)
    print("Example 3: Export Tools to JSON")
    print("=" * 60)

    # Generate tools
    openapi_yaml = """
openapi: 3.0.0
info:
  title: Weather API
  version: 1.0.0
paths:
  /weather/{city}:
    get:
      summary: Get weather for city
      operationId: getWeather
      parameters:
        - name: city
          in: path
          required: true
          schema:
            type: string
        - name: units
          in: query
          schema:
            type: string
            enum: [celsius, fahrenheit]
            default: celsius
      responses:
        '200':
          description: Weather data
"""

    loader = OpenAPILoader()
    spec = loader.load(openapi_yaml)

    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)

    generator = ToolGenerator()
    tools = generator.generate_tools(endpoints)

    registry = ToolRegistry(name="Weather API")
    registry.add_tools(tools)

    # Export to JSON
    print("\nExporting to JSON...")
    json_output = registry.to_json(indent=2)
    print(f"JSON output (first 500 chars):")
    print(json_output[:500])
    print("...")

    # Could also export to file:
    # registry.export_json("weather_tools.json")
    # registry.export_tools_only("weather_tools_array.json")

    print()


def example_4_grouped_parameters():
    """Example 4: Grouped parameter schemas."""
    print("=" * 60)
    print("Example 4: Grouped Parameter Schemas")
    print("=" * 60)

    openapi_yaml = """
openapi: 3.0.0
info:
  title: API with Multiple Parameter Types
  version: 1.0.0
paths:
  /items/{itemId}:
    put:
      summary: Update item
      operationId: updateItem
      parameters:
        - name: itemId
          in: path
          required: true
          schema:
            type: string
        - name: if-match
          in: header
          schema:
            type: string
        - name: notify
          in: query
          schema:
            type: boolean
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                name:
                  type: string
                price:
                  type: number
      responses:
        '200':
          description: Item updated
"""

    loader = OpenAPILoader()
    spec = loader.load(openapi_yaml)

    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)

    # Generate with grouped parameters
    print("\n--- Grouped Parameters (group_parameters=True) ---")
    generator_grouped = ToolGenerator(group_parameters=True)
    tools_grouped = generator_grouped.generate_tools(endpoints)

    for tool in tools_grouped:
        print(f"\nTool: {tool.name}")
        print(f"Input Schema Properties: {list(tool.inputSchema.get('properties', {}).keys())}")
        for prop_name, prop_schema in tool.inputSchema.get('properties', {}).items():
            print(f"  {prop_name}:")
            if prop_schema.get('type') == 'object':
                print(f"    Sub-properties: {list(prop_schema.get('properties', {}).keys())}")

    # Generate with flat parameters
    print("\n--- Flat Parameters (group_parameters=False) ---")
    generator_flat = ToolGenerator(group_parameters=False)
    tools_flat = generator_flat.generate_tools(endpoints)

    for tool in tools_flat:
        print(f"\nTool: {tool.name}")
        print(f"Input Schema Properties: {list(tool.inputSchema.get('properties', {}).keys())}")

    print()


def example_5_complete_workflow():
    """Example 5: Complete workflow from URL to MCP tools."""
    print("=" * 60)
    print("Example 5: Complete Workflow (URL → MCP Tools)")
    print("=" * 60)

    # For demonstration, using a sample spec
    # In production, you'd use: loader.load("https://api.example.com/openapi.json")

    print("\nWorkflow steps:")
    print("1. Load OpenAPI spec from URL")
    print("2. Normalize to canonical endpoints")
    print("3. Generate MCP tools")
    print("4. Register and organize tools")
    print("5. Export for use by MCP-compatible agents")

    # Simulated workflow
    sample_spec = """
openapi: 3.0.0
info:
  title: Complete API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List users
      operationId: listUsers
      tags: [users]
      responses:
        '200':
          description: User list
  /users/{userId}:
    get:
      summary: Get user
      operationId: getUser
      tags: [users]
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: User details
"""

    # Execute workflow
    loader = OpenAPILoader()
    spec = loader.load(sample_spec)
    print(f"✓ Loaded OpenAPI spec: {spec['info']['title']}")

    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)
    print(f"✓ Normalized {len(endpoints)} endpoints")

    generator = ToolGenerator(api_name="demo")
    tools = generator.generate_tools(endpoints)
    print(f"✓ Generated {len(tools)} MCP tools")

    registry = ToolRegistry(name="Demo API")
    registry.add_tools(tools)
    print(f"✓ Registered tools: {registry.get_tool_names()}")

    print("\n✓ Tools ready for MCP agent integration!")
    print(f"✓ Export with: registry.export_json('demo_tools.json')")

    print()


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Phase 2: MCP Tool Generation - Usage Examples")
    print("=" * 60 + "\n")

    # Run all examples
    example_1_basic_tool_generation()
    example_2_tool_registry()
    example_3_export_to_json()
    example_4_grouped_parameters()
    example_5_complete_workflow()

    print("=" * 60)
    print("All Phase 2 examples completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("  → Phase 3: Implement Runtime Execution Engine")
    print("  → Phase 4: Build Agent-Facing MCP Server")
