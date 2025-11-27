# Advanced Library Usage & Reference

This guide provides advanced usage patterns and comprehensive reference material for the REST-to-MCP Adapter library.

> **Note**: For basic usage and getting started, see the main [README.md](README.md).

## Table of Contents

- [Advanced Tool Generation](#advanced-tool-generation)
- [Custom Request Configuration](#custom-request-configuration)
- [Working with Registry](#working-with-registry)
- [Batch API Calls](#batch-api-calls)
- [Authentication Parameter Filtering](#authentication-parameter-filtering)
- [Complete Examples](#complete-examples)
- [Convenience Methods](#convenience-methods)
- [Integration Patterns](#integration-patterns)
- [API Reference](#api-reference)
- [Common Patterns](#common-patterns)
- [Troubleshooting](#troubleshooting)

---

## Advanced Tool Generation

### Filtering Tools During Generation

Generate only specific tools based on patterns:

```python
from adapter import ToolGenerator

generator = ToolGenerator(api_name="myapi")

# Generate only GET endpoints
get_tools = generator.generate_tools(
    endpoints,
    method_filter="GET"
)

# Generate first 10 tools only
limited_tools = generator.generate_tools(
    endpoints,
    limit=10
)

# Generate tools matching a path pattern
user_tools = generator.generate_tools(
    endpoints,
    path_pattern=r'/users'
)

# Combine filters
filtered_tools = generator.generate_tools(
    endpoints,
    method_filter="GET",
    path_pattern=r'/api/v1',
    limit=5
)
```

### Tool Name Customization

```python
registry = ToolRegistry(name="My API")
registry.add_tools(tools)

# Set up executor with authentication
executor = APIExecutor(
    base_url="https://api.example.com",
    auth=BearerAuth(token="your-token"),
    max_retries=3
)

# Create and run MCP server
server = MCPServer(
    name="My API Server",
    version="1.0.0",
    tool_registry=registry,
    executor=executor,
    endpoints=endpoints
)

server.run()  # Starts stdio server
```

### 2. Programmatic API Usage (Without MCP Server)

```python
from adapter import (
    OpenAPILoader,
    Normalizer,
    APIExecutor,
    BasicAuth
)

# Load and normalize
loader = OpenAPILoader()
spec = loader.load("path/to/openapi.yaml")
normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(spec)

# Set up executor
executor = APIExecutor(
    base_url="https://api.example.com",
    auth=BasicAuth(username="user", password="pass")
)

# Find an endpoint
endpoint = next(ep for ep in endpoints if ep.name == "get_users")

# Execute API call
result = executor.execute(
    endpoint=endpoint,
    parameters={"page": 1, "limit": 10}
)

# Handle response
if result.success:
    print(f"Data: {result.response.data}")
    print(f"Time: {result.execution_time_ms}ms")
else:
    print(f"Error: {result.response.error}")
```

### 3. Generate Tools Only (No Server)

```python
from adapter import OpenAPILoader, Normalizer, ToolGenerator, ToolRegistry

# Load and normalize
loader = OpenAPILoader()
spec = loader.load("https://api.example.com/openapi.json")
normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(spec)

# Generate tools
generator = ToolGenerator(api_name="example")
tools = generator.generate_tools(endpoints)

# Create registry
registry = ToolRegistry(name="Example API")
registry.add_tools(tools)

# Export to JSON
registry.export_json("tools.json")

# Search tools
search_results = registry.search_tools("user")
for tool in search_results:
    print(f"{tool.name}: {tool.description}")
```

## Important Limitations and Considerations

### MCP Tool Name Length Limit (64 Characters)

**Issue**: Claude's MCP protocol enforces a strict 64-character limit on tool names. APIs with long endpoint paths may exceed this limit.

**Automatic Solution**: The `ToolGenerator` automatically truncates long names by:
- Removing version numbers (v1, v2, v3)
- Removing API keywords (api, sapi, rest)
- Preserving the API prefix, HTTP method, and key path components
- Intelligently abbreviating long path segments

**Example**:
```python
# Original endpoint path: DELETE /sapi/v1/sub-account/subAccountApi/ipRestriction/ipList
# Generated name (73 chars): binance_delete_sapi_v1_sub_account_sub_account_api_ip_restriction_ip_list
# Auto-truncated (64 chars): binance_delete_sub_account_sub_account_ip_restriction_ip_list
```

**Impact on Your API**:
- ✅ **Most APIs**: No impact. Names are typically well under 64 characters
- ⚠️ **Large enterprise APIs** (like Binance): Some names may be truncated
- ❌ **Deeply nested REST APIs**: Very long paths may lose some specificity

**What You Should Know**:
1. Tool names are truncated **automatically** - no action required
2. The original full path is preserved in `tool.metadata["path"]`
3. Tool descriptions remain complete and unaffected
4. No functionality is lost - only the tool name is shortened

**Checking Your API**:
```python
from adapter import OpenAPILoader, Normalizer, ToolGenerator

loader = OpenAPILoader()
spec = loader.load("your-openapi-spec.yaml")
normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(spec)

generator = ToolGenerator(api_name="myapi")
tools = generator.generate_tools(endpoints)

# Check for truncated names
long_names = [t for t in tools if len(t.name) >= 60]
if long_names:
    print(f"⚠️ {len(long_names)} tools have names near the 64 char limit:")
    for tool in long_names:
        print(f"  {len(tool.name)} chars: {tool.name}")
        print(f"    Full path: {tool.metadata.get('path', 'N/A')}")
```

### OpenAPI $ref Resolution

**Issue**: Some OpenAPI specs use `$ref` pointers extensively (e.g., `{"$ref": "#/components/parameters/timestamp"}`).

**Solution**: The `OpenAPILoader` automatically dereferences all `$ref` pointers before normalization. This is handled transparently.

**No action needed** - just be aware that specs with circular references may fail to load.

## Authentication Options

### No Authentication

```python
from adapter import NoAuth, APIExecutor

executor = APIExecutor(
    base_url="https://api.example.com",
    auth=NoAuth()
)
```

### API Key Authentication

```python
from adapter import APIKeyAuth, APIExecutor

# Header-based API key
auth = APIKeyAuth(
    key="your-api-key",
    location="header",
    name="X-API-Key"
)

# Query parameter API key
auth = APIKeyAuth(
    key="your-api-key",
    location="query",
    name="api_key"
)

executor = APIExecutor(base_url="https://api.example.com", auth=auth)
```

### Bearer Token

```python
from adapter import BearerAuth, APIExecutor

auth = BearerAuth(token="your-bearer-token")
executor = APIExecutor(base_url="https://api.example.com", auth=auth)
```

### Basic Authentication

```python
from adapter import BasicAuth, APIExecutor

auth = BasicAuth(username="user", password="pass")
executor = APIExecutor(base_url="https://api.example.com", auth=auth)
```

### OAuth2

```python
from adapter import OAuth2Auth, APIExecutor

auth = OAuth2Auth(access_token="your-access-token")
executor = APIExecutor(base_url="https://api.example.com", auth=auth)
```

## Advanced Usage

### Custom Request Configuration

```python
from adapter import APIExecutor

executor = APIExecutor(
    base_url="https://api.example.com",
    auth=auth,
    timeout=60,                    # Request timeout in seconds
    max_retries=5,                 # Maximum retry attempts
    retry_backoff=2.0,             # Initial backoff time (exponential)
    retry_on_status_codes=[429, 500, 502, 503, 504]  # Retry on these codes
)
```

### Loading from Local Files

```python
from adapter import OpenAPILoader

loader = OpenAPILoader()

# Load from local file
spec = loader.load("/path/to/openapi.yaml")

# Or from URL
spec = loader.load("https://api.example.com/openapi.json")
```

### Working with Registry

```python
from adapter import ToolRegistry

registry = ToolRegistry(name="My API")
registry.add_tools(tools)

# Get all tools
all_tools = registry.get_all_tools()

# Get specific tool
tool = registry.get_tool("myapi_get_users")

# Search tools
results = registry.search_tools("user")

# Get tools by tag
tagged_tools = registry.get_tools_by_tag("users")

# Get tools by HTTP method
get_tools = registry.get_tools_by_method("GET")

# Count tools
count = registry.count()

# Export to JSON
registry.export_json("output.json")

# Import from JSON
registry = ToolRegistry.import_json("output.json")
```

### Batch API Calls

```python
from adapter import APIExecutor

executor = APIExecutor(base_url="https://api.example.com", auth=auth)

# Prepare batch calls
calls = [
    (endpoint1, {"id": "123"}),
    (endpoint2, {"name": "test"}),
    (endpoint3, {"page": 1}),
]

# Execute in sequence
results = executor.execute_batch(calls)

for result in results:
    if result.success:
        print(f"{result.endpoint_name}: {result.response.data}")
```

### Authentication Parameter Filtering

The adapter automatically filters authentication parameters from tool schemas so they don't appear as user-facing parameters. This uses a **hybrid approach** combining:

1. **Default common auth params** (signature, timestamp, api_key, authorization, etc.)
2. **Auto-detected params** from OpenAPI security schemes
3. **Custom overrides** for API-specific requirements

#### Automatic Filtering (Recommended)

```python
from adapter import OpenAPILoader, Normalizer, ToolGenerator

# Load OpenAPI spec
loader = OpenAPILoader()
spec = loader.load("https://api.example.com/openapi.yaml")

# Auto-detect auth parameters from security schemes
auth_params = loader.extract_auth_parameters(spec)
print(f"Auto-detected: {auth_params}")
# Output: {'x-api-key', 'signature', 'authorization'}

# Normalize endpoints
normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(spec)

# Generate tools with auto-detected + default auth params
generator = ToolGenerator(
    api_name="myapi",
    auto_detected_auth_params=auth_params  # Merged with defaults
)
tools = generator.generate_tools(endpoints)

# Auth parameters are automatically filtered from tool schemas
# Users only see business parameters (symbol, quantity, etc.)
```

#### Custom Auth Parameter Override

```python
# Override defaults completely with custom auth params
generator = ToolGenerator(
    api_name="myapi",
    auth_params={'my_signature', 'my_timestamp', 'my_nonce'}  # Only these filtered
)
```

#### Supported Security Scheme Types

The adapter automatically extracts auth parameters from these OpenAPI security types:

- **apiKey**: Extracts the explicit parameter name
  ```yaml
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-KEY  # ← Extracted
  ```

- **http** (bearer/basic/digest): Adds `authorization`
  ```yaml
  securitySchemes:
    BearerAuth:
      type: http
      scheme: bearer  # ← Adds "authorization"
  ```

- **oauth2**: Adds `authorization`, `access_token`, `token`
- **openIdConnect**: Adds `authorization`

#### Default Auth Parameters

These common auth parameters are filtered by default:

```python
DEFAULT_AUTH_PARAMS = {
    'signature', 'timestamp', 'recvwindow', 'recv_window',
    'api_key', 'apikey', 'api_secret', 'apisecret',
    'access_token', 'accesstoken', 'token',
    'authorization', 'auth',
    'nonce', 'sign',
}
```

#### Why Filter Auth Parameters?

Auth parameters should be handled by authentication handlers (like `BinanceAuth`, `BearerAuth`), not by end users:

```python
# ❌ Without filtering - users would need to provide auth params
tool_call(symbol="BTCUSDT", timestamp=1234567890, signature="abc123...")

# ✓ With filtering - auth handler adds them automatically
tool_call(symbol="BTCUSDT")  # Clean API!
```

## Complete Example: Dataforseo API

```python
#!/usr/bin/env python3
"""
Complete example: Using Dataforseo API as a library
"""
from adapter import (
    OpenAPILoader,
    Normalizer,
    ToolGenerator,
    ToolRegistry,
    APIExecutor,
    BasicAuth,
    MCPServer
)
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

# Configuration
DATAFORSEO_LOGIN = "your-login"
DATAFORSEO_PASSWORD = "your-password"
OPENAPI_URL = "https://raw.githubusercontent.com/dataforseo/open-ai-actions/refs/heads/master/dataforseo_researcher_toolkit.json"

# Phase 1: Load and normalize
loader = OpenAPILoader()
spec = loader.load(OPENAPI_URL)
normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(spec)

# Phase 2: Generate tools
generator = ToolGenerator(api_name="dataforseo")
tools = generator.generate_tools(endpoints)
registry = ToolRegistry(name="Dataforseo API")
registry.add_tools(tools)

# Save registry for later use
registry.export_json("dataforseo_registry.json")

# Phase 3: Set up executor
auth = BasicAuth(username=DATAFORSEO_LOGIN, password=DATAFORSEO_PASSWORD)
executor = APIExecutor(
    base_url="https://api.dataforseo.com",
    auth=auth,
    max_retries=3,
    timeout=30
)

# Phase 4: Create MCP server
server = MCPServer(
    name="Dataforseo MCP Server",
    version="1.0.0",
    tool_registry=registry,
    executor=executor,
    endpoints=endpoints
)

# Run the server
server.run()
```

## Convenience Methods

### Quick Registry Creation

For rapid prototyping and simple use cases, use the one-step convenience method:

```python
from adapter import ToolRegistry

# Create registry in one line
registry = ToolRegistry.create_from_openapi(
    "https://api.example.com/openapi.json"
)

# With configuration
registry = ToolRegistry.create_from_openapi(
    source="./specs/api.yaml",
    name="My API",
    api_name="myapi",
    limit=50,
    method_filter="GET"
)

# Registry is ready to use
print(f"Created {registry.count()} tools")
registry.export_json("tools.json")
```

**When to use the convenience method:**
- Quick prototyping and exploration
- Simple use cases with minimal configuration
- When you don't need access to intermediate objects (spec, endpoints, tools)

**When to use individual classes:**
- Complex workflows requiring intermediate processing
- Custom normalization or filtering logic
- Debugging or inspecting intermediate results
- Advanced configuration at each phase
- Reusing intermediate objects (spec, endpoints, tools)

### Simplified Server Creation

When using `create_from_openapi()`, you don't need to pass endpoints to MCPServer:

```python
from adapter import ToolRegistry, MCPServer, APIExecutor, BearerAuth

# Create registry with endpoints stored internally
registry = ToolRegistry.create_from_openapi("https://api.example.com/openapi.json")

# Set up executor
executor = APIExecutor(
    base_url="https://api.example.com",
    auth=BearerAuth(token="your-token")
)

# Create server - no endpoints parameter needed!
server = MCPServer(
    name="My API Server",
    version="1.0.0",
    tool_registry=registry,  # Contains endpoints
    executor=executor
    # endpoints parameter automatically retrieved from registry
)
server.run()
```

**How it works:**
- `create_from_openapi()` stores endpoints in the registry
- MCPServer checks if registry has endpoints
- If found, uses them automatically
- Backward compatible: explicit endpoints still work

## Integration Patterns

### Use with Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "my-api": {
      "command": "python",
      "args": ["/path/to/your/server.py"]
    }
  }
}
```

### Use as a Service

```python
import threading
from adapter import MCPServer

def run_server_in_thread(server):
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    return thread

# Start server in background
thread = run_server_in_thread(server)

# Do other work...
```

### Load Pre-generated Registry

#### Method 1: Using Built-in Import (Recommended)

```python
from adapter import ToolRegistry, APIExecutor, MCPServer, BasicAuth

# Load pre-generated registry (much faster than regenerating)
registry = ToolRegistry.import_json("dataforseo_registry.json")

# Set up executor
auth = BasicAuth(username="user", password="pass")
executor = APIExecutor(base_url="https://api.example.com", auth=auth)

# Note: You still need endpoints for execution
# Load endpoints if you need to execute tools
import json
from adapter.parsing import CanonicalEndpoint

with open("endpoints.json", "r") as f:
    endpoints = [CanonicalEndpoint(**data) for data in json.load(f)]
```

#### Method 2: Manual Loading with MCPTool (More Control)

```python
import json
from adapter import ToolRegistry, MCPTool, APIExecutor, MCPServer
from adapter.parsing import CanonicalEndpoint

# Load registry manually
registry_file = "binance_spot_toolkit.json"

with open(registry_file) as f:
    data = json.load(f)

# Create registry
registry = ToolRegistry(name=data.get("name", "API Tools"))

# Load tools manually
for tool_data in data.get("tools", []):
    tool = MCPTool(
        name=tool_data["name"],
        description=tool_data["description"],
        inputSchema=tool_data["inputSchema"],
        metadata=tool_data.get("metadata")
    )
    registry.add_tool(tool)

print(f"Loaded {registry.count()} tools")

# Load endpoints if needed for execution
endpoints_file = "binance_spot_endpoints.json"

with open(endpoints_file) as f:
    endpoint_data = json.load(f)

endpoints = [CanonicalEndpoint(**ep_data) for ep_data in endpoint_data]

# Now you can use the registry and endpoints with MCPServer
executor = APIExecutor(
    base_url="https://api.binance.com",
    auth=your_auth_handler
)

server = MCPServer(
    name="Binance MCP Server",
    version="1.0.0",
    tool_registry=registry,
    executor=executor,
    endpoints=endpoints
)

server.run()
```

**When to use manual loading:**
- When you need to filter or modify tools during loading
- When working with custom JSON formats
- When you want fine-grained control over the loading process
- When debugging tool definitions

#### When Do You Need Endpoints?

**Endpoints are ONLY needed if you plan to execute API calls.** Here's the breakdown:

```python
# Scenario 1: Just browsing/searching tools (NO endpoints needed)
registry = ToolRegistry.import_json("registry.json")
tools = registry.search_tools("user")
for tool in tools:
    print(f"{tool.name}: {tool.description}")
# ✅ Works without endpoints

# Scenario 2: Running MCP server that executes tools (endpoints REQUIRED)
registry = ToolRegistry.import_json("registry.json")

# Load endpoints - REQUIRED for execution
with open("endpoints.json") as f:
    endpoints = [CanonicalEndpoint(**data) for data in json.load(f)]

executor = APIExecutor(base_url="...", auth=auth)
server = MCPServer(
    name="API Server",
    version="1.0.0",
    tool_registry=registry,
    executor=executor,
    endpoints=endpoints  # ✅ REQUIRED here
)
server.run()

# Scenario 3: Direct API execution (endpoints REQUIRED)
with open("endpoints.json") as f:
    endpoints = [CanonicalEndpoint(**data) for data in json.load(f)]

executor = APIExecutor(base_url="...", auth=auth)
result = executor.execute(endpoints[0], arguments={"param": "value"})
# ✅ Endpoints required for execution
```

**Summary:**
- **Tool browsing/export**: Endpoints NOT needed
- **MCP server with execution**: Endpoints REQUIRED
- **Direct API calls**: Endpoints REQUIRED

## API Reference

For detailed API documentation, see the docstrings in each module:

- **Phase 1**: `adapter.ingestion`, `adapter.parsing`
- **Phase 2**: `adapter.mcp`
- **Phase 3**: `adapter.runtime`
- **Phase 4**: `adapter.server`

## Common Patterns

### Pattern 1: One-time Setup, Multiple Runs

```python
# setup.py - Run once to generate registry
from adapter import OpenAPILoader, Normalizer, ToolGenerator, ToolRegistry

loader = OpenAPILoader()
spec = loader.load("https://api.example.com/openapi.json")
normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(spec)

generator = ToolGenerator(api_name="example")
tools = generator.generate_tools(endpoints)
registry = ToolRegistry(name="Example API")
registry.add_tools(tools)

# Save for reuse
registry.export_json("registry.json")

# Save endpoints for later use (needed for tool execution)
import json
with open("endpoints.json", "w") as f:
    json.dump([ep.model_dump() for ep in endpoints], f)
```

```python
# server.py - Run this to start the server
from adapter import ToolRegistry, APIExecutor, MCPServer, BearerAuth

# Load pre-generated registry
registry = ToolRegistry.import_json("registry.json")

# Load endpoints
import json
from adapter.parsing import CanonicalEndpoint
with open("endpoints.json", "r") as f:
    endpoints = [CanonicalEndpoint(**data) for data in json.load(f)]

# Set up and run server
executor = APIExecutor(
    base_url="https://api.example.com",
    auth=BearerAuth(token="token")
)

server = MCPServer(
    name="Example Server",
    version="1.0.0",
    tool_registry=registry,
    executor=executor,
    endpoints=endpoints
)

server.run()
```

### Pattern 2: Dynamic Tool Discovery

```python
from adapter import ToolRegistry

registry = ToolRegistry.import_json("registry.json")

# Find tools related to "user"
user_tools = registry.search_tools("user")

# Filter by method
get_tools = [t for t in user_tools if t.metadata.get("method") == "GET"]

# Execute specific tools
for tool in get_tools:
    print(f"Tool: {tool.name}")
    print(f"Description: {tool.description}")
    print(f"Parameters: {tool.inputSchema['properties'].keys()}")
```

## Troubleshooting

### Import Errors

If you get import errors, make sure the package is installed:

```bash
pip install -e .
```

### Authentication Issues

Enable debug logging to see request details:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Tool-Endpoint Mapping

If tools aren't executing correctly, check the mapping:

```python
from adapter.server import ExecutionHandler

handler = ExecutionHandler(tool_provider, executor, endpoints)

# Check the mapping
for tool_name, endpoint in handler._tool_endpoint_map.items():
    print(f"{tool_name} -> {endpoint.name}")
```

## Support

For issues, questions, or contributions, please visit the GitHub repository.
