# REST-to-MCP Adapter

**A Python library for converting OpenAPI specifications into MCP (Model Context Protocol) tools for AI agents.**

Transform any REST API with an OpenAPI/Swagger specification into tools that Claude, GPT, and other LLM-powered agents can use.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Quick Start

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

# 1. Load OpenAPI spec
loader = OpenAPILoader()
spec = loader.load("https://api.example.com/openapi.json")

# 2. Normalize to canonical format
normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(spec)

# 3. Generate MCP tools (auth params auto-filtered!)
generator = ToolGenerator(api_name="myapi")
tools = generator.generate_tools(endpoints)

# 4. Create tool registry
registry = ToolRegistry(name="My API")
registry.add_tools(tools)

# 5. Set up API executor with authentication
executor = APIExecutor(
    base_url="https://api.example.com",
    auth=BearerAuth(token="your-token")
)

# 6. Start MCP server (for Claude Desktop, etc.)
server = MCPServer(
    name="My API Server",
    version="1.0.0",
    tool_registry=registry,
    executor=executor,
    endpoints=endpoints
)
server.run()  # Claude can now use your API!
```

---

## 📦 Installation

### From Source (Recommended for now)

```bash
git clone https://github.com/your-username/rest-to-mcp-adapter.git
cd rest-to-mcp-adapter
pip install -e .
```

### Dependencies

```bash
# Core dependencies (auto-installed)
pydantic>=2.0.0
pyyaml>=6.0
requests>=2.31.0

# Optional but recommended
langchain-community>=0.0.20
```

---

## ✨ Key Features

### 🔄 OpenAPI Ingestion
- **Load from anywhere**: URL, file path, or raw JSON/YAML
- **Full spec support**: OpenAPI 3.x and Swagger 2.x
- **Auto-detection**: Automatically determines input type
- **$ref dereferencing**: Resolves all JSON pointer references

### 🛠️ MCP Tool Generation
- **Automatic conversion**: OpenAPI endpoints → MCP tools
- **Smart naming**: 64-character limit with intelligent truncation
- **Auth filtering**: Automatically hides auth parameters from users
- **Hybrid approach**: Defaults + auto-detection + custom overrides

### 🔐 Authentication Support
- **Built-in handlers**: API Key, Bearer, Basic, OAuth2
- **Custom handlers**: Easy to implement your own
- **Automatic parameter filtering**: Auth params hidden from tool schemas
- **Conditional auth**: Only applies to endpoints that require it

### ⚡ Runtime Execution
- **Direct API calls**: Execute REST requests from canonical endpoints
- **Retry logic**: Exponential backoff for failed requests
- **Error handling**: Comprehensive error types and messages
- **Response processing**: JSON, text, and binary support

### 🤖 MCP Server
- **Full MCP protocol**: JSON-RPC 2.0 over stdio
- **Claude integration**: Ready for Claude Desktop
- **Tool discovery**: `tools/list` endpoint
- **Tool execution**: `tools/call` endpoint

---

## 📖 Detailed Usage

### 1. Loading OpenAPI Specifications

```python
from adapter import OpenAPILoader

loader = OpenAPILoader()

# From URL
spec = loader.load("https://api.example.com/openapi.json")

# From file
spec = loader.load("./specs/api.yaml")

# From raw content
yaml_content = """
openapi: 3.0.0
info:
  title: My API
  version: 1.0.0
paths:
  /users:
    get:
      summary: List users
"""
spec = loader.load(yaml_content)

# Auto-detection works for all methods
spec = loader.load(source)  # Detects URL, file, or content automatically
```

### 2. Normalizing to Canonical Format

```python
from adapter import Normalizer

normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(spec)

# Inspect normalized endpoints
for endpoint in endpoints:
    print(f"{endpoint.method} {endpoint.path}")
    print(f"  Name: {endpoint.name}")
    print(f"  Parameters: {len(endpoint.parameters)}")
    print(f"  Requires auth: {bool(endpoint.security)}")
```

### 3. Generating MCP Tools

#### Basic Usage

```python
from adapter import ToolGenerator

generator = ToolGenerator(api_name="myapi")
tools = generator.generate_tools(endpoints)

# Tools are ready to use!
for tool in tools:
    print(f"Tool: {tool.name}")
    print(f"Description: {tool.description}")
    print(f"Parameters: {tool.inputSchema}")
```

#### With Auto-Detected Auth Filtering

```python
from adapter import OpenAPILoader, ToolGenerator

# Load spec
loader = OpenAPILoader()
spec = loader.load("api.yaml")

# Auto-detect auth parameters from security schemes
auto_detected = loader.extract_auth_parameters(spec)
print(f"Auto-detected: {auto_detected}")
# Output: {'x-api-key', 'signature', ...}

# Generate tools with hybrid filtering (defaults + auto-detected)
generator = ToolGenerator(
    api_name="myapi",
    auto_detected_auth_params=auto_detected
)
tools = generator.generate_tools(endpoints)

# Auth parameters are automatically hidden!
# Users only see business parameters
```

#### With Custom Auth Parameters

```python
# Override defaults completely
generator = ToolGenerator(
    api_name="myapi",
    auth_params={'my_signature', 'my_timestamp', 'my_nonce'}
)
tools = generator.generate_tools(endpoints)
```

### 4. Working with Tool Registry

```python
from adapter import ToolRegistry

# Create registry
registry = ToolRegistry(name="My API")
registry.add_tools(tools)

# Query tools
print(f"Total tools: {registry.count()}")
print(f"Tool names: {registry.get_tool_names()}")

# Filter tools
product_tools = registry.get_tools_by_tag("products")
get_tools = registry.get_tools_by_method("GET")
search_results = registry.search_tools("user")

# Get specific tool
user_tool = registry.get_tool("myapi_get_users")

# Export/Import
registry.export_json("tools.json")
registry2 = ToolRegistry.import_json("tools.json")
```

### 5. Authentication Handlers

#### Built-in Handlers

```python
from adapter import APIExecutor, BearerAuth, APIKeyAuth, BasicAuth

# Bearer Token
executor = APIExecutor(
    base_url="https://api.example.com",
    auth=BearerAuth(token="your-bearer-token")
)

# API Key (in header)
executor = APIExecutor(
    base_url="https://api.example.com",
    auth=APIKeyAuth(api_key="your-api-key", header_name="X-API-Key")
)

# API Key (in query)
executor = APIExecutor(
    base_url="https://api.example.com",
    auth=APIKeyAuth(api_key="your-api-key", location="query", param_name="apikey")
)

# Basic Auth
executor = APIExecutor(
    base_url="https://api.example.com",
    auth=BasicAuth(username="user", password="pass")
)
```

#### Custom Auth Handler

```python
from adapter.runtime import AuthHandler

class CustomAuth(AuthHandler):
    def __init__(self, api_key: str, api_secret: str):
        self.api_key = api_key
        self.api_secret = api_secret

    def apply(self, headers: dict, params: dict) -> None:
        # Add custom authentication logic
        import time
        import hmac
        import hashlib

        timestamp = int(time.time() * 1000)
        params["timestamp"] = str(timestamp)

        # Create signature
        query_string = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        signature = hmac.new(
            self.api_secret.encode(),
            query_string.encode(),
            hashlib.sha256
        ).hexdigest()

        params["signature"] = signature
        headers["X-API-KEY"] = self.api_key

# Use custom auth
executor = APIExecutor(
    base_url="https://api.example.com",
    auth=CustomAuth(api_key="key", api_secret="secret")
)
```

### 6. Executing API Calls Directly

```python
from adapter import APIExecutor, NoAuth

# Create executor
executor = APIExecutor(
    base_url="https://api.example.com",
    auth=NoAuth(),  # Public endpoints
    timeout=30,
    max_retries=3
)

# Find an endpoint
endpoint = next(ep for ep in endpoints if ep.name == "get_users")

# Execute call
result = executor.execute(endpoint, arguments={"limit": 10})

if result.success:
    print(f"Status: {result.status_code}")
    print(f"Data: {result.response.data}")
else:
    print(f"Error: {result.error}")
```

### 7. Running an MCP Server

```python
from adapter import MCPServer

# Create server (combines registry + executor + endpoints)
server = MCPServer(
    name="My API Server",
    version="1.0.0",
    tool_registry=registry,
    executor=executor,
    endpoints=endpoints
)

# Run server (stdio transport for Claude Desktop)
server.run()
```

#### Configure in Claude Desktop

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "myapi": {
      "command": "python",
      "args": ["/path/to/your/server.py"]
    }
  }
}
```

---

## 🔐 Authentication Parameter Filtering

One of the most powerful features is **automatic authentication parameter filtering**. This ensures users never see or need to provide auth-related parameters.

### How It Works

The library uses a **hybrid approach** combining:

1. **Default common parameters**: `signature`, `timestamp`, `api_key`, `authorization`, etc.
2. **Auto-detected from OpenAPI**: Extracts from `securitySchemes`
3. **Custom overrides**: You can specify your own

### Default Auth Parameters

```python
DEFAULT_AUTH_PARAMS = {
    'signature', 'timestamp', 'recvwindow', 'recv_window',
    'api_key', 'apikey', 'api_secret', 'apisecret',
    'access_token', 'accesstoken', 'token',
    'authorization', 'auth',
    'nonce', 'sign',
}
```

### Auto-Detection Example

```python
loader = OpenAPILoader()
spec = loader.load("api.yaml")

# Extract auth params from securitySchemes
auth_params = loader.extract_auth_parameters(spec)
# Returns: {'x-api-key', 'signature', ...}

# Use in tool generation
generator = ToolGenerator(
    api_name="myapi",
    auto_detected_auth_params=auth_params
)
```

### Supported Security Schemes

| Type | Auto-Detected Parameters |
|------|--------------------------|
| `apiKey` | Parameter name from spec |
| `http` (bearer/basic) | `authorization` |
| `oauth2` | `authorization`, `access_token`, `token` |
| `openIdConnect` | `authorization` |

### Example: Before vs After

**Without filtering** (❌ Bad):
```python
# User sees auth parameters
tool.inputSchema = {
    "properties": {
        "symbol": {"type": "string"},
        "timestamp": {"type": "integer"},  # ❌ Exposed
        "signature": {"type": "string"}     # ❌ Exposed
    }
}

# User has to provide them (confusing!)
client.call_tool("get_price", {
    "symbol": "BTCUSDT",
    "timestamp": 1234567890,      # ❌ User shouldn't know this
    "signature": "abc123..."       # ❌ User shouldn't know this
})
```

**With filtering** (✅ Good):
```python
# User only sees business parameters
tool.inputSchema = {
    "properties": {
        "symbol": {"type": "string"}  # ✅ Only what matters
    }
}

# Clean API!
client.call_tool("get_price", {
    "symbol": "BTCUSDT"  # ✅ Simple and clear
})
# Auth handler adds timestamp and signature automatically
```

---

## 🏗️ Architecture Overview

```
OpenAPI Spec (URL/file/content)
    ↓
OpenAPILoader → Parses and dereferences $refs
    ↓
Normalizer → Converts to CanonicalEndpoint models
    ↓
ToolGenerator → Creates MCP tool definitions
    ↓
ToolRegistry → Organizes and manages tools
    ↓
MCPServer → Exposes tools via JSON-RPC (stdio)
    ↓
Claude/GPT → Calls tools
    ↓
APIExecutor → Executes actual REST API calls
    ↓
Response → Returns to agent
```

For detailed architecture documentation, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## 📚 Examples

### Complete Example: Building a Binance MCP Server

```python
#!/usr/bin/env python3
"""Binance API MCP Server"""
from adapter import (
    OpenAPILoader, Normalizer, ToolGenerator,
    ToolRegistry, APIExecutor, MCPServer
)
from my_auth import BinanceAuth  # Your custom auth handler

# 1. Load Binance OpenAPI spec
loader = OpenAPILoader()
spec = loader.load(
    "https://raw.githubusercontent.com/binance/binance-api-swagger/master/spot_api.yaml"
)

# 2. Auto-detect auth parameters
auto_detected = loader.extract_auth_parameters(spec)

# 3. Normalize endpoints
normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(spec)
print(f"Loaded {len(endpoints)} endpoints")

# 4. Generate tools with auth filtering
generator = ToolGenerator(
    api_name="binance",
    auto_detected_auth_params=auto_detected
)
tools = generator.generate_tools(endpoints)

# 5. Create registry
registry = ToolRegistry(name="Binance Spot API")
registry.add_tools(tools)

# 6. Set up executor with custom auth
executor = APIExecutor(
    base_url="https://api.binance.com",
    auth=BinanceAuth(
        api_key="your-key",
        api_secret="your-secret"
    )
)

# 7. Create and run MCP server
server = MCPServer(
    name="Binance MCP Server",
    version="1.0.0",
    tool_registry=registry,
    executor=executor,
    endpoints=endpoints
)

if __name__ == "__main__":
    server.run()
```

### More Examples

See the `examples/` directory for more:
- `examples/basic_usage.py` - Basic ingestion and normalization
- `examples/phase2_tool_generation.py` - Tool generation examples
- `examples/phase3_execution.py` - API execution examples
- `examples/phase4_mcp_server.py` - MCP server setup

---

## 🧪 Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=adapter

# Run specific test
pytest tests/test_tool_generator.py
```

---

## 🛣️ Roadmap

- ✅ **Phase 1**: OpenAPI ingestion and normalization
- ✅ **Phase 2**: MCP tool generation
- ✅ **Phase 3**: Runtime execution engine
- ✅ **Phase 4**: MCP server implementation
- 🔄 **Phase 5**: Additional loaders (Postman, GraphQL)
- 📋 **Future**: WebSocket transport, enhanced caching

---

## 🤝 Contributing

Contributions welcome! The core library is complete, and we're looking for:

- Additional authentication methods
- Performance optimizations
- More loaders (Postman collections, GraphQL schemas)
- Documentation improvements
- Real-world usage examples

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙋 Support

- **Issues**: [GitHub Issues](https://github.com/your-username/rest-to-mcp-adapter/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-username/rest-to-mcp-adapter/discussions)

---

**Built with ❤️ for the AI agent ecosystem**
