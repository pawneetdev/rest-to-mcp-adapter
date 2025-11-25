# REST-to-MCP Adapter

**A Python library for converting REST API specifications into MCP (Model Context Protocol) tools for AI agents.**

Transform any REST API specification into tools that Claude, GPT, and other LLM-powered agents can use.

**Supported Formats:**
- OpenAPI 3.x (JSON, YAML)
- Swagger 2.x (JSON, YAML)
- OpenAPI Actions format (JSON)

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

### From PyPI

```bash
pip install rest-to-mcp-adapter
```

### From Source

```bash
git clone https://github.com/pawneetdev/rest-to-mcp-adapter.git
cd rest-to-mcp-adapter
pip install -e .
```

### Development Installation

```bash
# Clone and install with development dependencies
git clone https://github.com/pawneetdev/rest-to-mcp-adapter.git
cd rest-to-mcp-adapter
pip install -e ".[dev]"
```

### Dependencies

Core dependencies (automatically installed):
- `pydantic>=2.0.0` - Data validation and modeling
- `pyyaml>=6.0` - YAML parsing
- `requests>=2.31.0` - HTTP client
- `langchain-community>=0.0.20` - MCP protocol support

---

## ✨ Key Features

### 🔄 Specification Ingestion
- **Multiple formats**: OpenAPI 3.x, Swagger 2.x, OpenAPI Actions
- **JSON & YAML**: Full support for both formats
- **Load from anywhere**: URL, file path, or raw content
- **Auto-detection**: Automatically determines input type and format
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

> **💡 Looking for advanced features?** See [LIBRARY_USAGE.md](LIBRARY_USAGE.md) for:
> - Advanced tool generation patterns
> - Registry operations (search, filter, export/import)
> - Batch API calls
> - Integration patterns and best practices
> - Troubleshooting guide
> - Important limitations (64-char tool name limit, etc.)

### 1. Loading API Specifications

The library supports multiple specification formats with automatic detection:

```python
from adapter import OpenAPILoader

loader = OpenAPILoader()

# OpenAPI 3.x (JSON)
spec = loader.load("https://api.example.com/openapi.json")

# OpenAPI 3.x (YAML)
spec = loader.load("./specs/openapi.yaml")

# Swagger 2.x (JSON)
spec = loader.load("./specs/swagger.json")

# Swagger 2.x (YAML)
spec = loader.load("https://api.example.com/swagger.yaml")

# OpenAPI Actions format
spec = loader.load("./specs/actions.json")

# From raw YAML content
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

# From raw JSON content
json_content = '{"openapi": "3.0.0", "info": {"title": "My API"}}'
spec = loader.load(json_content)

# Auto-detection works for all methods
# Automatically detects: URL vs file vs content, JSON vs YAML, OpenAPI vs Swagger
spec = loader.load(source)
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

**Real-World Example**: The [Binance MCP](https://github.com/pawneetdev/binance-mcp) implements a production-grade version of this pattern with additional features:
- Server time synchronization for timestamp accuracy
- Query string canonicalization (sorted parameter ordering)
- Optional `recvWindow` parameter for clock skew tolerance
- Comprehensive error messages for auth failures

Refer to its `auth.py` module for a complete implementation you can adapt for similar signature-based APIs.

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

For complete, production-ready MCP server implementations with full source code, see the [Real-World Integrations](#-real-world-integrations) section below.

---

## 🌍 Real-World Integrations

The REST-to-MCP Adapter powers production MCP servers for real APIs. These example repositories demonstrate complete implementations with different authentication patterns and specification formats.

### DataForSEO MCP

**Repository**: https://github.com/pawneetdev/dataforseo-mcp/

Production MCP server for the DataForSEO API demonstrating:

- **Authentication**: HTTP Basic Authentication
- **Spec Format**: OpenAPI Actions/JSON format
- **Use Case**: SEO data retrieval and analysis
- **What You'll Learn**:
  - Loading OpenAPI JSON specifications
  - Implementing standard HTTP Basic auth
  - Organizing tools by API categories
  - Handling paginated responses

**Quick Start**:
```bash
git clone https://github.com/pawneetdev/dataforseo-mcp.git
cd dataforseo-mcp
pip install -e .
```

See the repository README for complete setup instructions and Claude Desktop integration.

---

### Binance MCP

**Repository**: https://github.com/pawneetdev/binance-mcp

Production MCP server for the Binance Spot Trading API demonstrating:

- **Authentication**: Custom HMAC-SHA256 signature-based authentication
- **Spec Format**: Swagger/OpenAPI YAML format
- **Use Case**: Cryptocurrency trading and market data
- **What You'll Learn**:
  - Loading Swagger YAML specifications
  - Implementing custom `AuthHandler` with cryptographic signatures
  - Query string signing with HMAC-SHA256
  - Automatic timestamp and nonce injection
  - Advanced parameter filtering for signature-based endpoints
  - Handling large APIs (100+ endpoints)

**Authentication Pattern**:
The Binance MCP extends the `AuthHandler` base class to implement Binance's specific requirements:
- API key in headers (`X-MBX-APIKEY`)
- Timestamp query parameter (synchronized with server time)
- HMAC-SHA256 signature of query string
- Optional `recvWindow` for timing flexibility

This pattern can be adapted for other APIs with signature-based authentication (AWS, Kraken, etc.).

**Quick Start**:
```bash
git clone https://github.com/pawneetdev/binance-mcp.git
cd binance-mcp
pip install -e .
```

See the repository README for API key setup, credential management, and Claude Desktop integration.

---

### Learning Path

1. **Start with DataForSEO**: Straightforward authentication, standard OpenAPI patterns
2. **Progress to Binance**: Advanced custom authentication, complex parameter handling
3. **Build Your Own**: Apply these patterns to your target API

Both repositories include:
- Complete source code and project structure
- Production-grade error handling
- Retry logic and timeout management
- Claude Desktop configuration examples
- Deployment documentation

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

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

Copyright (c) 2025 Pawneet Singh

---

## 🙋 Support

- **Issues**: [GitHub Issues](https://github.com/pawneetdev/rest-to-mcp-adapter/issues)

---

**Built with ❤️ for the AI agent ecosystem**
