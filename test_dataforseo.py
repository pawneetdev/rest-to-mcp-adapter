"""
Test file for Dataforseo API - Demonstrates complete workflow.

This file shows:
- Phase 1: Load and normalize OpenAPI spec
- Phase 2: Generate MCP tools
- Phase 3: Execute actual API calls (NEW!)
"""

from adapter.ingestion import OpenAPILoader
from adapter.parsing import Normalizer
from adapter.mcp import ToolGenerator, ToolRegistry

# Phase 3: Import runtime execution components
from adapter.runtime import (
    APIExecutor,
    APIKeyAuth,
    BearerAuth,
    NoAuth,
)
import json


def phase1_and_2_load_and_generate():
    """Phase 1 & 2: Load OpenAPI and generate MCP tools."""
    print("\n" + "=" * 70)
    print("PHASE 1: Loading and Normalizing OpenAPI Spec")
    print("=" * 70)

    # Load OpenAPI spec
    loader = OpenAPILoader()
    spec = loader.load(
        "https://raw.githubusercontent.com/dataforseo/open-ai-actions/refs/heads/master/dataforseo_researcher_toolkit.json"
    )
    print(f"✓ Loaded OpenAPI spec")

    # Normalize to canonical format
    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)
    print(f"✓ Normalized {len(endpoints)} endpoints")

    # Show some endpoint details
    print("\nFirst 3 endpoints:")
    for i, endpoint in enumerate(endpoints[:3]):
        print(f"  {i+1}. {endpoint.name}: {endpoint.method} {endpoint.path}")
        print(f"     Description: {endpoint.description[:60]}...")
        print(f"     Parameters: {len(endpoint.parameters)}")

    print("\n" + "=" * 70)
    print("PHASE 2: Generating MCP Tools")
    print("=" * 70)

    # Generate MCP tools
    generator = ToolGenerator(api_name="dataforseo")
    tools = generator.generate_tools(endpoints)
    print(f"✓ Generated {len(tools)} MCP tools")

    # Show first tool structure
    print("\nFirst tool structure:")
    print(f"  Name: {tools[0].name}")
    print(f"  Description: {tools[0].description[:80]}...")
    print(f"  Input Schema Keys: {list(tools[0].inputSchema.keys())}")
    if 'properties' in tools[0].inputSchema:
        print(f"  Parameters: {list(tools[0].inputSchema['properties'].keys())[:5]}")

    # Create registry
    registry = ToolRegistry(name="Dataforseo researcher toolkit")
    registry.add_tools(tools)
    print(f"\n✓ Created registry: {registry}")

    # Export to JSON
    registry.export_json("dataforseo_researcher_toolkit.json")
    print(f"✓ Exported tools to: dataforseo_researcher_toolkit.json")

    # Show registry stats
    print(f"\nRegistry Stats:")
    print(f"  Total tools: {registry.count()}")
    print(f"  All tags: {registry.get_all_tags()}")

    # Filter examples
    post_tools = registry.get_tools_by_method("POST")
    print(f"  POST endpoints: {len(post_tools)}")

    return endpoints, registry


def phase3_execute_api_calls(endpoints):
    """Phase 3: Execute actual API calls using the runtime engine."""
    print("\n" + "=" * 70)
    print("PHASE 3: Runtime Execution Engine")
    print("=" * 70)

    # ============================================================
    # IMPORTANT: Dataforseo API requires authentication!
    # You need to provide your API credentials to actually execute calls.
    # ============================================================

    print("\n📌 Authentication Setup:")
    print("-" * 70)
    print("Dataforseo API requires authentication. Choose one option:\n")

    print("Option 1: API Key in Header")
    print("  auth = APIKeyAuth(")
    print("      key='your-api-key',")
    print("      location='header',")
    print("      name='Authorization'  # or 'X-API-Key'")
    print("  )")

    print("\nOption 2: Basic Authentication (username:password)")
    print("  from adapter.runtime import BasicAuth")
    print("  auth = BasicAuth(")
    print("      username='your-login',")
    print("      password='your-password'")
    print("  )")

    print("\nOption 3: Bearer Token")
    print("  auth = BearerAuth(token='your-bearer-token')")

    print("\nOption 4: No Auth (for public endpoints only)")
    print("  auth = NoAuth()")

    # For demonstration, we'll use NoAuth (won't actually work without credentials)
    auth = NoAuth()
    print(f"\n✓ Using: {auth}")
    print("  Note: Replace with actual authentication to execute real calls!")

    # ============================================================
    # Create the API Executor
    # ============================================================

    print("\n📌 Creating API Executor:")
    print("-" * 70)

    executor = APIExecutor(
        base_url="https://api.dataforseo.com",  # Base URL for Dataforseo API
        auth=auth,                               # Authentication handler
        max_retries=3,                           # Retry failed requests up to 3 times
        retry_backoff=1.0,                       # Start with 1s backoff, doubles each retry
        timeout=30,                              # Request timeout in seconds
    )

    print(f"✓ Executor created with configuration:")
    print(f"  Base URL: https://api.dataforseo.com")
    print(f"  Authentication: {auth}")
    print(f"  Max Retries: 3")
    print(f"  Retry Backoff: 1.0s (exponential)")
    print(f"  Timeout: 30s")

    # ============================================================
    # Example: Executing an API call
    # ============================================================

    print("\n📌 How to Execute an API Call:")
    print("-" * 70)

    # Find an endpoint to execute
    # Let's find a simple GET endpoint
    example_endpoint = None
    for endpoint in endpoints:
        if endpoint.method == "GET":
            example_endpoint = endpoint
            break

    if example_endpoint:
        print(f"\nExample endpoint: {example_endpoint.name}")
        print(f"  Method: {example_endpoint.method}")
        print(f"  Path: {example_endpoint.path}")
        print(f"  Description: {example_endpoint.description[:80]}...")

        # Show required parameters
        required_params = [p for p in example_endpoint.parameters if p.required]
        optional_params = [p for p in example_endpoint.parameters if not p.required]

        print(f"\n  Required parameters ({len(required_params)}):")
        for param in required_params[:5]:  # Show first 5
            print(f"    - {param.name} ({param.location.value}): {param.description[:50]}...")

        if optional_params:
            print(f"\n  Optional parameters ({len(optional_params)}):")
            for param in optional_params[:3]:  # Show first 3
                print(f"    - {param.name} ({param.location.value}): {param.description[:50]}...")

        print("\n  To execute this endpoint:")
        print("  " + "-" * 66)
        print("  result = executor.execute(")
        print(f"      endpoint=example_endpoint,")
        print("      parameters={")
        for param in required_params[:2]:
            print(f"          '{param.name}': 'your_value_here',")
        print("      }")
        print("  )")
        print()
        print("  # Handle the response")
        print("  if result.success:")
        print("      print(f'Success! Status: {result.response.status_code}')")
        print("      print(f'Data: {result.response.data}')")
        print("      print(f'Execution time: {result.execution_time_ms}ms')")
        print("  else:")
        print("      print(f'Failed: {result.response.error}')")
        print("      print(f'Status: {result.response.status_code}')")
        print("      print(f'Attempts: {result.attempts}')")

        # ============================================================
        # Commented out actual execution (requires valid credentials)
        # ============================================================

        print("\n  Actual execution (COMMENTED OUT - needs valid credentials):")
        print("  " + "-" * 66)
        print("""
        # Uncomment and provide real parameter values to execute:
        #
        # result = executor.execute(
        #     endpoint=example_endpoint,
        #     parameters={
        #         # Fill in required parameters here
        #     }
        # )
        #
        # if result.success:
        #     print(f"✓ API call succeeded!")
        #     print(f"  Status Code: {result.response.status_code}")
        #     print(f"  Execution Time: {result.execution_time_ms:.2f}ms")
        #     print(f"  Response Data:")
        #     print(json.dumps(result.response.data, indent=2))
        # else:
        #     print(f"✗ API call failed!")
        #     print(f"  Error: {result.response.error}")
        #     print(f"  Status Code: {result.response.status_code}")
        #     print(f"  Attempts Made: {result.attempts}")
        """)

    # ============================================================
    # Show complete workflow example
    # ============================================================

    print("\n📌 Complete Workflow Example:")
    print("-" * 70)
    print("""
# 1. Find the endpoint you want to call
my_endpoint = None
for ep in endpoints:
    if 'specific_name' in ep.name:
        my_endpoint = ep
        break

# 2. Prepare parameters based on endpoint requirements
parameters = {}
for param in my_endpoint.parameters:
    if param.required:
        # You must provide values for required parameters
        parameters[param.name] = 'your_value'
    else:
        # Optional parameters can be omitted
        parameters[param.name] = 'optional_value'

# 3. Execute the API call
result = executor.execute(
    endpoint=my_endpoint,
    parameters=parameters
)

# 4. Handle the response
if result.success:
    # Success! Process the data
    data = result.response.data
    print(f"Got data: {data}")
else:
    # Failed - check the error
    print(f"Error: {result.response.error}")
    print(f"Status: {result.response.status_code}")
    """)


def main():
    """Run the complete demonstration."""
    print("\n" + "=" * 70)
    print("UNIVERSAL REST → MCP ADAPTER")
    print("Complete Workflow: Load → Normalize → Generate → Execute")
    print("=" * 70)

    # Phase 1 & 2: Load and generate tools
    endpoints, registry = phase1_and_2_load_and_generate()

    # Phase 3: Show how to execute API calls
    phase3_execute_api_calls(endpoints)

    print("\n" + "=" * 70)
    print("✓ DEMONSTRATION COMPLETE")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Add your Dataforseo API credentials")
    print("2. Uncomment the execution code")
    print("3. Fill in the required parameters")
    print("4. Run the script to execute real API calls!")
    print()
    print("Files generated:")
    print("- dataforseo_researcher_toolkit.json (MCP tools export)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
