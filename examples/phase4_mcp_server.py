"""
Phase 4: MCP Server Examples

This file demonstrates how to create and run an MCP server that exposes
REST API tools to LLM agents like Claude.

The MCP server integrates all previous phases:
- Phase 1: Load and normalize OpenAPI specs
- Phase 2: Generate MCP tool definitions
- Phase 3: Execute actual API calls
- Phase 4: Expose tools via MCP protocol

Examples:
1. Basic MCP server setup
2. Server with authentication
3. Complete workflow: OpenAPI → MCP Server
4. Testing the MCP server
"""

import logging
import sys

from adapter.ingestion import OpenAPILoader
from adapter.parsing import Normalizer
from adapter.mcp import ToolGenerator, ToolRegistry
from adapter.runtime import APIExecutor, BearerAuth, NoAuth, APIKeyAuth
from adapter.server import MCPServer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr  # Log to stderr so it doesn't interfere with MCP stdio
)

logger = logging.getLogger(__name__)


def example1_basic_server():
    """
    Example 1: Basic MCP server with public API.

    This example creates an MCP server for a public API that doesn't
    require authentication.
    """
    print("=" * 70, file=sys.stderr)
    print("Example 1: Basic MCP Server (Public API)", file=sys.stderr)
    print("=" * 70, file=sys.stderr)

    # Phase 1: Load and normalize OpenAPI spec
    logger.info("Loading OpenAPI spec...")
    loader = OpenAPILoader()
    spec = loader.load("https://petstore3.swagger.io/api/v3/openapi.json")

    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)
    logger.info(f"Loaded {len(endpoints)} endpoints")

    # Phase 2: Generate MCP tools
    logger.info("Generating MCP tools...")
    generator = ToolGenerator(api_name="petstore")
    tools = generator.generate_tools(endpoints)

    registry = ToolRegistry(name="Petstore API")
    registry.add_tools(tools)
    logger.info(f"Generated {len(tools)} tools")

    # Phase 3: Create API executor
    logger.info("Creating API executor...")
    executor = APIExecutor(
        base_url="https://petstore3.swagger.io/api/v3",
        auth=NoAuth(),  # Public API, no auth needed
        max_retries=3,
        timeout=30
    )

    # Phase 4: Create and run MCP server
    logger.info("Creating MCP server...")
    server = MCPServer(
        name="Petstore MCP Server",
        version="1.0.0",
        tool_registry=registry,
        executor=executor,
        endpoints=endpoints
    )

    logger.info("MCP server ready - starting stdio transport")
    logger.info("Connect your MCP client to interact with the server")

    # Run the server (blocks until stopped)
    server.run()


def example2_authenticated_server():
    """
    Example 2: MCP server with API authentication.

    This example shows how to create an MCP server for an API that
    requires authentication.
    """
    print("=" * 70, file=sys.stderr)
    print("Example 2: MCP Server with Authentication", file=sys.stderr)
    print("=" * 70, file=sys.stderr)

    # Configuration
    API_URL = "https://api.example.com/openapi.json"
    BASE_URL = "https://api.example.com"
    API_TOKEN = "your-api-token-here"  # Replace with actual token

    logger.info("Loading OpenAPI spec...")
    loader = OpenAPILoader()

    # Note: Using petstore for demonstration since we need a real API
    spec = loader.load("https://petstore3.swagger.io/api/v3/openapi.json")

    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)

    # Generate tools
    generator = ToolGenerator(api_name="example")
    tools = generator.generate_tools(endpoints)
    registry = ToolRegistry(name="Example API")
    registry.add_tools(tools)

    # Create executor with authentication
    # Choose the appropriate auth method for your API:

    # Option 1: Bearer token
    auth = BearerAuth(token=API_TOKEN)

    # Option 2: API key in header
    # auth = APIKeyAuth(key=API_TOKEN, location="header", name="X-API-Key")

    # Option 3: API key in query parameter
    # auth = APIKeyAuth(key=API_TOKEN, location="query", name="api_key")

    executor = APIExecutor(
        base_url="https://petstore3.swagger.io/api/v3",  # Replace with BASE_URL
        auth=auth,
        max_retries=3,
        timeout=30
    )

    # Create MCP server
    server = MCPServer(
        name="Authenticated API MCP Server",
        version="1.0.0",
        tool_registry=registry,
        executor=executor,
        endpoints=endpoints
    )

    logger.info("MCP server with authentication ready")
    server.run()


def example3_complete_workflow():
    """
    Example 3: Complete workflow with custom OpenAPI spec.

    This is a complete end-to-end example that you can customize
    for your specific API.
    """
    print("=" * 70, file=sys.stderr)
    print("Example 3: Complete MCP Server Workflow", file=sys.stderr)
    print("=" * 70, file=sys.stderr)

    # ========================================
    # CONFIGURATION - Customize these values
    # ========================================

    OPENAPI_URL = "https://petstore3.swagger.io/api/v3/openapi.json"
    API_BASE_URL = "https://petstore3.swagger.io/api/v3"
    API_NAME = "petstore"
    SERVER_NAME = "Petstore MCP Server"
    SERVER_VERSION = "1.0.0"

    # Authentication (choose one)
    USE_AUTH = False
    AUTH_TOKEN = "your-token-here"

    # ========================================
    # PHASE 1: Load and Normalize
    # ========================================

    logger.info("PHASE 1: Loading and normalizing OpenAPI spec")
    loader = OpenAPILoader()
    spec = loader.load(OPENAPI_URL)

    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)
    logger.info(f"✓ Loaded {len(endpoints)} endpoints")

    # Show some endpoint details
    logger.info("Sample endpoints:")
    for i, endpoint in enumerate(endpoints[:3]):
        logger.info(f"  {i+1}. {endpoint.name}: {endpoint.method} {endpoint.path}")

    # ========================================
    # PHASE 2: Generate MCP Tools
    # ========================================

    logger.info("PHASE 2: Generating MCP tools")
    generator = ToolGenerator(api_name=API_NAME)
    tools = generator.generate_tools(endpoints)

    registry = ToolRegistry(name=f"{API_NAME} API")
    registry.add_tools(tools)
    logger.info(f"✓ Generated {len(tools)} MCP tools")

    # ========================================
    # PHASE 3: Create API Executor
    # ========================================

    logger.info("PHASE 3: Creating API executor")

    if USE_AUTH:
        auth = BearerAuth(token=AUTH_TOKEN)
        logger.info(f"✓ Using Bearer authentication")
    else:
        auth = NoAuth()
        logger.info(f"✓ No authentication")

    executor = APIExecutor(
        base_url=API_BASE_URL,
        auth=auth,
        max_retries=3,
        retry_backoff=1.0,
        timeout=30
    )
    logger.info(f"✓ Executor configured with base URL: {API_BASE_URL}")

    # ========================================
    # PHASE 4: Create and Run MCP Server
    # ========================================

    logger.info("PHASE 4: Creating MCP server")
    server = MCPServer(
        name=SERVER_NAME,
        version=SERVER_VERSION,
        tool_registry=registry,
        executor=executor,
        endpoints=endpoints
    )

    logger.info("=" * 70)
    logger.info(f"MCP Server Ready!")
    logger.info(f"  Name: {SERVER_NAME}")
    logger.info(f"  Version: {SERVER_VERSION}")
    logger.info(f"  Tools: {registry.count()}")
    logger.info(f"  Base URL: {API_BASE_URL}")
    logger.info(f"  Authentication: {auth}")
    logger.info("=" * 70)
    logger.info("Starting stdio transport - connect your MCP client")
    logger.info("=" * 70)

    # Run the server
    server.run()


def main():
    """
    Main entry point - choose which example to run.
    """
    import sys

    if len(sys.argv) > 1:
        example = sys.argv[1]

        if example == "1" or example == "basic":
            example1_basic_server()
        elif example == "2" or example == "auth":
            example2_authenticated_server()
        elif example == "3" or example == "complete":
            example3_complete_workflow()
        else:
            print(f"Unknown example: {example}", file=sys.stderr)
            print_usage()
    else:
        # Default: run complete workflow
        example3_complete_workflow()


def print_usage():
    """Print usage instructions."""
    print("\nUsage: python phase4_mcp_server.py [example]", file=sys.stderr)
    print("\nExamples:", file=sys.stderr)
    print("  1, basic    - Basic MCP server (public API)", file=sys.stderr)
    print("  2, auth     - MCP server with authentication", file=sys.stderr)
    print("  3, complete - Complete workflow (default)", file=sys.stderr)
    print("\nThe MCP server runs on stdio and can be connected to MCP clients.", file=sys.stderr)
    print("\nTo test the server, you can:", file=sys.stderr)
    print("  1. Run the server: python phase4_mcp_server.py", file=sys.stderr)
    print("  2. Connect with an MCP client (e.g., Claude Desktop, inspector)", file=sys.stderr)
    print("  3. Or test manually with examples/test_mcp_server.py", file=sys.stderr)
    print()


if __name__ == "__main__":
    main()
