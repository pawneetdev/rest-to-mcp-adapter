# Universal REST → MCP Adapter

A production-quality framework for converting **any** REST API documentation into **MCP-compatible tools** for Large Language Models and agent systems.

## 🎯 Project Vision

This system transforms diverse API documentation formats (OpenAPI, HTML, Postman, GraphQL, PDF, etc.) into a unified canonical format that can be used to generate MCP tools for LLM-powered agents.

### Supported Formats (Planned)

| Format | Phase 1 | Future Phases |
|--------|---------|---------------|
| OpenAPI/Swagger (JSON/YAML) | ✅ | - |
| HTML Documentation | ✅ | LLM extraction + recursive crawling |
| Postman Collections | - | ✅ |
| GraphQL Schemas | - | ✅ |
| Markdown Documentation | - | ✅ |
| PDF Documentation | - | ✅ |

## 🚀 Current Status

### Phase 1: Ingestion & Normalization ✅ (Completed)

The **foundation layer** provides:

- **OpenAPI Loader**: Parse OpenAPI 3.x and Swagger 2.x from URLs, files, or raw content
- **HTML Loader**: Extract clean text from HTML docs (URLs or raw HTML)
- **Canonical Models**: Pydantic-based unified data model
- **Normalizer**: Convert raw data to canonical endpoint format
- **LangChain Integration**: Optional integration for enhanced parsing

### Phase 2: MCP Tool Generation ✅ (Completed)

The **MCP integration layer** provides:

- **Tool Generator**: Convert canonical endpoints to MCP tool definitions
- **Schema Converter**: Transform canonical schemas to JSON Schema
- **Tool Registry**: Manage and organize generated tools
- **Export Functionality**: Export tools to JSON for MCP agents

### Phase 3: Runtime Execution Engine ✅ (Completed)

The **runtime execution layer** provides:

- **API Executor**: Execute actual REST API calls from canonical endpoints
- **Authentication Handlers**: Support for API Key, Bearer, Basic, OAuth2
- **Request Builder**: Build HTTP requests with path/query/header/body parameters
- **Response Processor**: Parse and normalize API responses
- **Error Handling**: Automatic retries with exponential backoff
- **Comprehensive Examples**: Real-world usage patterns

### Phase 4: MCP Server ✅ (Completed)

The **MCP server layer** provides:

- **MCP Server**: Complete Model Context Protocol server implementation
- **Stdio Transport**: JSON-RPC communication via standard input/output
- **Tool Discovery**: Expose REST API tools to LLM agents
- **Tool Execution**: Execute API calls through MCP protocol
- **Claude Integration**: Ready to use with Claude Desktop and other MCP clients
- **Full Pipeline Integration**: Combines all previous phases into a complete system

### What's NOT Yet Implemented

- ❌ LLM-based HTML/PDF parsing (Phase 5)
- ❌ Extended loaders: Postman/GraphQL (Phase 6)
- ❌ Recursive HTML crawling (Phase 7)

## 📦 Installation

### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/pawneetdev/rest-to-mcp-adapter.git
cd rest-to-mcp-adapter

# Create a virtual environment with uv
uv venv

# Activate the virtual environment
# On Linux/Mac:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

### Using pip (Alternative)

```bash
# Clone the repository
git clone https://github.com/pawneetdev/rest-to-mcp-adapter.git
cd rest-to-mcp-adapter

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

- **pydantic** ≥2.0.0 - Data validation and canonical models
- **PyYAML** ≥6.0 - YAML parsing
- **beautifulsoup4** ≥4.12.0 - HTML parsing
- **requests** ≥2.31.0 - HTTP requests for URL loading
- **langchain-community** ≥0.0.20 - LangChain integration (optional but recommended)

## 🏗️ Architecture

```
adapter/
├── ingestion/              # Loaders for different formats
│   ├── base_loader.py      # Abstract loader interface
│   ├── loader_openapi.py   # OpenAPI/Swagger loader
│   └── loader_html.py      # HTML documentation loader
├── parsing/                # Normalization and canonical models
│   ├── canonical_models.py # Pydantic models
│   └── normalizer.py       # Data normalization
├── mcp/                    # MCP tool generation (Phase 2)
│   ├── tool_generator.py   # Convert endpoints to MCP tools
│   ├── schema_converter.py # JSON Schema conversion
│   └── tool_registry.py    # Tool management
├── runtime/                # Runtime execution engine (Phase 3)
│   ├── auth.py             # Authentication handlers
│   ├── request_builder.py  # Build HTTP requests
│   ├── executor.py         # Execute API calls
│   └── response.py         # Response processing
├── server/                 # MCP server (Phase 4)
│   ├── server.py           # Main MCP server
│   ├── transport.py        # Stdio transport layer
│   ├── tool_provider.py    # Tool discovery
│   └── execution_handler.py # Tool execution
└── pipeline/               # Convenience helpers
    └── ingestion_pipeline.py # Helper functions
```

### Key Design Principles

1. **Simplicity**: No format detection - users call the appropriate loader directly
2. **Flexibility**: Load from URLs, file paths, or raw content
3. **Extensibility**: Easy to add new loaders for additional formats
4. **LangChain Integration**: Leverage existing utilities where available
5. **Resilience**: Graceful handling of partial/malformed specs
6. **Type Safety**: Pydantic models for validation

## 📚 Usage

### Quick Start

```python
from adapter.ingestion import OpenAPILoader
from adapter.parsing import Normalizer

# Load OpenAPI from URL
loader = OpenAPILoader()
spec = loader.load("https://api.example.com/openapi.json")

# Or from file
spec = loader.load_from_file("./specs/api.yaml")

# Or from raw content
spec = loader.load(yaml_content)

# Normalize to canonical format
normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(spec)

for endpoint in endpoints:
    print(f"{endpoint.name}: {endpoint.method} {endpoint.path}")
```

### Example 1: OpenAPI from URL

```python
from adapter.ingestion import OpenAPILoader
from adapter.parsing import Normalizer

# Load from URL
loader = OpenAPILoader()
spec = loader.load_from_url("https://petstore3.swagger.io/api/v3/openapi.json")

# Normalize
normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(spec)

# Access canonical data
for endpoint in endpoints:
    print(f"{endpoint.name}: {endpoint.method} {endpoint.path}")
    for param in endpoint.parameters:
        print(f"  - {param.name} ({param.location}): {param.type}")
```

### Example 2: OpenAPI from File

```python
from adapter.ingestion import OpenAPILoader

loader = OpenAPILoader()

# Load from file path
spec = loader.load_from_file("./specs/api.yaml")

# Or let it auto-detect
spec = loader.load("./specs/api.yaml")  # Auto-detects file path
```

### Example 3: HTML from URL

```python
from adapter.ingestion import HTMLLoader

loader = HTMLLoader()

# Load from URL
clean_text = loader.load_from_url("https://docs.example.com/api")

# Or let it auto-detect
clean_text = loader.load("https://docs.example.com/api")

# Clean text is ready for LLM extraction (Phase 2)
print(clean_text)
```

### Example 4: HTML from Raw Content

```python
from adapter.ingestion import HTMLLoader

html_content = """
<html>
<head><title>API Docs</title></head>
<body>
    <h1>GET /api/products</h1>
    <p>Retrieve all products.</p>
</body>
</html>
"""

loader = HTMLLoader()
clean_text = loader.load(html_content)
print(clean_text)  # Scripts, styles, nav removed
```

### Example 5: Convenience Functions

```python
from adapter.pipeline import load_openapi, load_html

# Quick prototyping
spec = load_openapi("https://api.example.com/openapi.json")
text = load_html("https://docs.example.com/api")
```

### Complete Examples

See `examples/basic_usage.py` for comprehensive usage examples:

```bash
python examples/basic_usage.py
```

### Phase 2: MCP Tool Generation

Once you have normalized endpoints, you can convert them to MCP-compatible tool definitions:

```python
from adapter.ingestion import OpenAPILoader
from adapter.parsing import Normalizer
from adapter.mcp import ToolGenerator, ToolRegistry

# Step 1: Load and normalize
loader = OpenAPILoader()
spec = loader.load("https://api.example.com/openapi.json")

normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(spec)

# Step 2: Generate MCP tools
generator = ToolGenerator(api_name="example")
tools = generator.generate_tools(endpoints)

# Step 3: Register and organize
registry = ToolRegistry(name="Example API Tools")
registry.add_tools(tools)

# Step 4: Export for MCP agents
registry.export_json("example_tools.json")

# Query tools
print(f"Total tools: {registry.count()}")
print(f"Tools: {registry.get_tool_names()}")

# Filter by tags or HTTP method
product_tools = registry.get_tools_by_tag("products")
post_tools = registry.get_tools_by_method("POST")
```

#### MCP Tool Structure

Each generated MCP tool includes:

```python
MCPTool(
    name="example__get_user_by_id",      # API name + endpoint name
    description="Get user by ID...",      # Full description with usage
    inputSchema={                         # JSON Schema for parameters
        "type": "object",
        "properties": {
            "user_id": {
                "type": "string",
                "description": "User identifier"
            }
        },
        "required": ["user_id"]
    },
    metadata={                            # REST endpoint metadata
        "method": "GET",
        "path": "/users/{user_id}",
        "tags": ["users"]
    }
)
```

#### Grouped vs Flat Parameters

You can choose how parameters are organized:

```python
# Flat (default): All parameters at the same level
generator = ToolGenerator(group_parameters=False)
# Input schema: {"user_id": "...", "include_details": "...", ...}

# Grouped: Parameters grouped by location
generator = ToolGenerator(group_parameters=True)
# Input schema: {"path": {"user_id": "..."}, "query": {"include_details": "..."}}
```

#### Complete Phase 2 Examples

See `examples/phase2_mcp_tools.py` for comprehensive examples:

```bash
python examples/phase2_mcp_tools.py
```

### Phase 3: Runtime Execution

Execute actual REST API calls using canonical endpoints:

```python
from adapter.ingestion import OpenAPILoader
from adapter.parsing import Normalizer
from adapter.runtime import APIExecutor, BearerAuth

# Step 1: Load and normalize
loader = OpenAPILoader()
spec = loader.load("https://api.example.com/openapi.json")

normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(spec)

# Step 2: Configure authentication
auth = BearerAuth(token="your-api-token")

# Step 3: Create executor
executor = APIExecutor(
    base_url="https://api.example.com",
    auth=auth,
    max_retries=3,
    timeout=30
)

# Step 4: Execute API calls
result = executor.execute(
    endpoint=endpoints[0],
    parameters={"user_id": "123", "include": "profile"}
)

# Step 5: Handle response
if result.success:
    print(f"Data: {result.response.data}")
    print(f"Time: {result.execution_time_ms}ms")
else:
    print(f"Error: {result.response.error}")
```

#### Authentication Options

The runtime supports multiple authentication methods:

```python
from adapter.runtime import NoAuth, APIKeyAuth, BearerAuth, BasicAuth, OAuth2Auth

# No authentication
auth = NoAuth()

# API Key in header
auth = APIKeyAuth(key="your-key", location="header", name="X-API-Key")

# API Key in query parameter
auth = APIKeyAuth(key="your-key", location="query", name="api_key")

# Bearer token
auth = BearerAuth(token="your-bearer-token")

# Basic authentication
auth = BasicAuth(username="user", password="pass")

# OAuth2
auth = OAuth2Auth(access_token="your-oauth-token")
```

#### Error Handling and Retries

The executor automatically retries on transient failures:

```python
executor = APIExecutor(
    base_url="https://api.example.com",
    max_retries=3,                          # Retry up to 3 times
    retry_backoff=1.0,                      # Start with 1s, doubles each retry
    retry_on_status_codes=[429, 500, 502, 503, 504],  # Retry these codes
    timeout=30                              # Request timeout in seconds
)

result = executor.execute(endpoint=my_endpoint, parameters=params)

print(f"Attempts: {result.attempts}")      # How many tries it took
print(f"Success: {result.success}")        # Whether it succeeded
print(f"Time: {result.execution_time_ms}ms")
```

#### Complete Phase 3 Examples

See `examples/phase3_runtime_execution.py` for comprehensive examples:

```bash
python examples/phase3_runtime_execution.py
```

### Phase 4: MCP Server

Create an MCP server that exposes your REST API tools to LLM agents like Claude:

```python
from adapter.ingestion import OpenAPILoader
from adapter.parsing import Normalizer
from adapter.mcp import ToolGenerator, ToolRegistry
from adapter.runtime import APIExecutor, BearerAuth
from adapter.server import MCPServer

# Steps 1-2: Load and normalize (Phase 1)
loader = OpenAPILoader()
spec = loader.load("https://api.example.com/openapi.json")

normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(spec)

# Step 3: Generate MCP tools (Phase 2)
generator = ToolGenerator(api_name="example")
tools = generator.generate_tools(endpoints)

registry = ToolRegistry(name="Example API")
registry.add_tools(tools)

# Step 4: Create executor (Phase 3)
executor = APIExecutor(
    base_url="https://api.example.com",
    auth=BearerAuth(token="your-token"),
    max_retries=3
)

# Step 5: Create and run MCP server (Phase 4)
server = MCPServer(
    name="Example API MCP Server",
    version="1.0.0",
    tool_registry=registry,
    executor=executor,
    endpoints=endpoints
)

# Run the server (stdio transport)
server.run()
```

#### Using with Claude Desktop

Configure your MCP server in Claude Desktop's config file:

**MacOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "example-api": {
      "command": "python",
      "args": ["/path/to/your/mcp_server.py"]
    }
  }
}
```

Claude will automatically connect to your MCP server and gain access to all your REST API tools!

#### MCP Server Features

- **JSON-RPC 2.0**: Standard protocol for MCP communication
- **Tool Discovery**: `tools/list` - List all available API tools
- **Tool Execution**: `tools/call` - Execute any API endpoint
- **Stdio Transport**: Communication via standard input/output
- **Error Handling**: Proper JSON-RPC error responses
- **Logging**: Comprehensive logging for debugging

#### Testing Your MCP Server

```bash
# Run the server
python examples/phase4_mcp_server.py

# Or test it with the test script
python examples/test_mcp_server.py
```

#### Complete Phase 4 Examples

See `examples/phase4_mcp_server.py` for comprehensive examples:

```bash
# Run basic example
python examples/phase4_mcp_server.py basic

# Run with authentication
python examples/phase4_mcp_server.py auth

# Run complete workflow
python examples/phase4_mcp_server.py complete
```

## 🔌 Extensibility

### No Format Detection

The adapter uses a **simple, explicit design** - users call the appropriate loader directly:

```python
from adapter.ingestion import OpenAPILoader, HTMLLoader

# Call the right loader for your format
openapi_loader = OpenAPILoader()
html_loader = HTMLLoader()
```

**Why no format detection?**
- Simpler API - explicit is better than implicit
- Users know their format
- Reduces complexity and potential errors
- Easier to extend and maintain

### Adding Custom Loaders

The framework is designed for easy extension:

```python
from adapter.ingestion.base_loader import BaseLoader

class PostmanLoader(BaseLoader):
    def load(self, content: str) -> dict:
        # Parse Postman collection
        import json
        return json.loads(content)

    def load_from_url(self, url: str) -> dict:
        # Fetch and parse from URL
        pass
```

### Future Loader Support

The architecture is ready for:
- **Postman Collections**: Import Postman collection JSON (from URL/file)
- **GraphQL Schemas**: Parse GraphQL schema definitions
- **Markdown Docs**: Extract endpoints from Markdown
- **PDF Docs**: Extract text and parse with LLM

## 🌐 URL and File Support

All loaders support multiple input methods:

### OpenAPI Loader

```python
loader = OpenAPILoader()

# From URL
spec = loader.load_from_url("https://api.example.com/openapi.json")

# From file path
spec = loader.load_from_file("./specs/api.yaml")

# From raw content
spec = loader.load(yaml_content)

# Auto-detect (URL, file, or content)
spec = loader.load("https://api.example.com/openapi.json")  # Detects URL
spec = loader.load("./specs/api.yaml")  # Detects file
spec = loader.load('{"openapi": "3.0.0"}')  # Detects content
```

### HTML Loader

```python
loader = HTMLLoader()

# From URL
text = loader.load_from_url("https://docs.example.com/api")

# From raw HTML
text = loader.load(html_content)

# Auto-detect
text = loader.load("https://docs.example.com/api")  # Detects URL
text = loader.load("<html>...</html>")  # Detects content
```

## 🔄 Future Enhancement: Recursive HTML Crawling

The HTML loader can be extended to **recursively crawl** linked documentation pages to discover all API endpoints across an entire documentation site:

```python
# Future API (not yet implemented)
loader = HTMLLoader(recursive=True, max_depth=3)
all_content = loader.load_from_url("https://docs.api.com")
# Would crawl all linked pages and aggregate content
```

**How it would work:**
1. Start at the root documentation URL
2. Extract all internal links
3. Recursively follow links up to max_depth
4. Deduplicate URLs to avoid re-processing
5. Aggregate content from all pages
6. Return combined, cleaned text ready for LLM extraction

## 📊 Canonical Data Model

All endpoints are normalized to a consistent format:

```python
CanonicalEndpoint(
    name="get_user_by_id",           # snake_case identifier
    method="GET",                     # HTTP method
    path="/users/{user_id}",          # URL path
    description="Get user by ID",     # Description
    summary="Get user",               # Brief summary
    parameters=[                      # All parameters
        CanonicalParameter(
            name="user_id",
            location="path",          # query|path|header|body
            type="number",            # string|number|boolean|object|array
            required=True,
            description="User identifier"
        )
    ],
    body_schema=None,                 # Request body schema
    response_schema=CanonicalSchema(...),  # Response schema
    tags=["users"],                   # Categorization
    deprecated=False                  # Deprecation status
)
```

## 🧪 Data Types & Normalization

### Type Normalization

All types are normalized to:
- `string` - Text data
- `number` - Numeric data (int/float)
- `boolean` - True/false
- `object` - Nested objects
- `array` - Lists/arrays
- `null` - Null values

### Parameter Locations

All locations are normalized to:
- `query` - URL query parameters
- `path` - URL path parameters
- `header` - HTTP headers
- `body` - Request body
- `cookie` - Cookie parameters

### Naming Conventions

All identifiers are converted to `snake_case`:
- `getUserById` → `get_user_by_id`
- `CreateNewOrder` → `create_new_order`
- `fetch-products` → `fetch_products`

## 🛣️ Roadmap

### Phase 1: Ingestion & Normalization ✅ (Completed)
- Direct loader calls (no format detection)
- OpenAPI/HTML loaders with URL/file support
- Canonical models
- Normalization pipeline

### Phase 2: MCP Tool Generation ✅ (Completed)
- Generate MCP tool definitions from canonical endpoints
- Tool metadata generation
- Parameter validation schemas
- Tool registry with filtering and export
- JSON Schema conversion for parameter validation

### Phase 3: Runtime Execution Engine ✅ (Completed)
- REST API call execution with canonical endpoints
- Authentication handling (API Key, Bearer, Basic, OAuth2)
- Request building with parameter routing (path/query/header/body)
- Response processing and parsing (JSON, text)
- Error handling with automatic retries and exponential backoff
- Comprehensive authentication options

### Phase 4: Agent-Facing MCP Server ✅ (Completed)
- Complete MCP server implementation with JSON-RPC 2.0
- Stdio transport for communication
- Tool discovery (tools/list) and execution (tools/call)
- Integration with Claude Desktop and other MCP clients
- Full pipeline: OpenAPI → Tools → Execution → MCP Server

### Phase 5: LLM-Based Extraction
- HTML → structured endpoints (via LLM)
- PDF → structured endpoints (via LLM)
- Markdown → structured endpoints (via LLM)
- Unstructured docs → structured endpoints

### Phase 6: Extended Loaders
- Postman collection loader (URL/file support)
- GraphQL schema loader
- Markdown documentation loader
- PDF documentation loader (with LLM extraction)

### Phase 7: HTML Recursive Crawling
- Implement recursive crawling for HTML loaders
- Follow internal links across documentation sites
- Deduplicate and aggregate content
- Support configurable crawl depth and URL filtering

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions are welcome! We've completed all core phases (1-4): Ingestion, Tool Generation, Runtime Execution, and MCP Server. Phase 5+ focuses on advanced features.

Areas for contribution:
- LLM-based extraction for HTML/PDF/Markdown docs (Phase 5)
- Additional loaders: Postman, GraphQL, etc. (Phase 6)
- Recursive HTML crawling implementation (Phase 7)
- WebSocket transport for MCP server
- Enhanced normalization logic
- Additional authentication methods (OAuth2 flow, custom headers)
- Performance optimizations
- Documentation improvements
- Test coverage
- Real-world use case examples

## 📞 Support

For issues and questions:
- GitHub Issues: [Issues](https://github.com/pawneetdev/rest-to-mcp-adapter/issues)
- Discussions: [Discussions](https://github.com/pawneetdev/rest-to-mcp-adapter/discussions)

---

**Built with** ❤️ **for the LLM agent ecosystem**
