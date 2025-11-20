# Using REST-to-MCP Adapter as a Library

This guide shows how to use the REST-to-MCP Adapter as a Python library in your own projects.

## Installation

### From Source (Development)

```bash
# Clone the repository
git clone <repository-url>
cd rest-to-mcp-adapter

# Install in editable mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### From PyPI (Coming Soon)

```bash
pip install rest-to-mcp-adapter
```

## Quick Start

### 1. Basic Usage: Create an MCP Server

```python
from adapter import (
    OpenAPILoader,
    Normalizer,
    ToolGenerator,
    ToolRegistry,
    APIExecutor,
    BearerAuth,
    MCPServer
)

# Load OpenAPI spec
loader = OpenAPILoader()
spec = loader.load("https://api.example.com/openapi.json")

# Normalize endpoints
normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(spec)

# Generate MCP tools
generator = ToolGenerator(api_name="myapi")
tools = generator.generate_tools(endpoints)

# Create registry
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

```python
from adapter import ToolRegistry, APIExecutor, MCPServer, BasicAuth

# Load pre-generated registry (much faster than regenerating)
registry = ToolRegistry.import_json("dataforseo_registry.json")

# Set up executor
auth = BasicAuth(username="user", password="pass")
executor = APIExecutor(base_url="https://api.example.com", auth=auth)

# Note: You still need endpoints for execution
# You can save them alongside the registry
import json
with open("endpoints.json", "r") as f:
    endpoints_data = json.load(f)
# Reconstruct endpoints from saved data
```

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

# Save endpoints too
import json
with open("endpoints.json", "w") as f:
    json.dump([ep.dict() for ep in endpoints], f)
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
