# Architecture Documentation

This document provides detailed technical information about the REST-to-MCP Adapter's architecture, design decisions, and internal workings.

## Table of Contents

- [System Overview](#system-overview)
- [Phase Breakdown](#phase-breakdown)
- [Canonical Data Model](#canonical-data-model)
- [Directory Structure](#directory-structure)
- [Design Decisions](#design-decisions)
- [Extension Points](#extension-points)

---

## System Overview

The REST-to-MCP Adapter follows a **pipeline architecture** with four distinct phases:

```
Phase 1: Ingestion & Normalization
    ↓
Phase 2: MCP Tool Generation
    ↓
Phase 3: Runtime Execution
    ↓
Phase 4: MCP Server
```

Each phase is independent and can be used standalone or as part of the complete pipeline.

---

## Phase Breakdown

### Phase 1: Ingestion & Normalization

**Purpose**: Load API documentation from various sources and convert to a unified canonical format.

**Components**:

#### OpenAPILoader (`adapter/ingestion/loader_openapi.py`)
- Loads OpenAPI 3.x and Swagger 2.x specifications
- Supports URLs, file paths, and raw content
- **$ref Dereferencing**: Resolves all JSON Pointer references
- Integrates with LangChain for enhanced parsing

**Key Methods**:
```python
load(source: str) -> Dict[str, Any]
load_from_url(url: str) -> Dict[str, Any]
load_from_file(path: str) -> Dict[str, Any]
extract_auth_parameters(spec: Dict) -> Set[str]
```

#### Normalizer (`adapter/parsing/normalizer.py`)
- Converts raw OpenAPI specs to canonical endpoints
- Handles parameter extraction and normalization
- Extracts security requirements
- Generates snake_case names

**Key Methods**:
```python
normalize_openapi(spec: Dict) -> List[CanonicalEndpoint]
```

---

### Phase 2: MCP Tool Generation

**Purpose**: Convert canonical endpoints into MCP-compatible tool definitions.

**Components**:

#### ToolGenerator (`adapter/mcp/tool_generator.py`)
- Generates MCP tool definitions from canonical endpoints
- Handles auth parameter filtering (hybrid approach)
- Implements intelligent name truncation (64-char limit)
- Creates JSON Schema for tool inputs

**Key Features**:
- **Auth Filtering**: Removes auth params from user-facing schemas
- **Name Truncation**: Intelligently shortens long names
- **Metadata**: Includes method, path, tags, response schema

#### SchemaConverter (`adapter/mcp/schema_converter.py`)
- Converts canonical schemas to JSON Schema
- Handles nested objects and arrays
- Maps canonical types to JSON Schema types

#### ToolRegistry (`adapter/mcp/tool_registry.py`)
- Stores and manages MCP tools
- Provides search and filtering capabilities
- Export/import functionality

**Key Methods**:
```python
add_tool(tool: MCPTool)
get_tool(name: str) -> MCPTool
get_tools_by_tag(tag: str) -> List[MCPTool]
search_tools(query: str) -> List[MCPTool]
export_json(path: str)
```

---

### Phase 3: Runtime Execution

**Purpose**: Execute actual REST API calls from canonical endpoints.

**Components**:

#### APIExecutor (`adapter/runtime/executor.py`)
- Executes HTTP requests based on canonical endpoints
- Applies authentication conditionally
- Handles retries with exponential backoff
- Processes responses

**Key Features**:
- **Conditional Auth**: Only applies auth if `endpoint.security` is non-empty
- **Retry Logic**: Configurable retries with backoff
- **Error Handling**: Comprehensive error types

#### RequestBuilder (`adapter/runtime/request_builder.py`)
- Builds HTTP requests from canonical endpoints
- Routes parameters to correct locations (path/query/header/body)
- Validates required parameters

#### AuthHandler (`adapter/runtime/auth/`)
- **NoAuth**: For public endpoints
- **APIKeyAuth**: API key in header or query
- **BearerAuth**: Bearer token authentication
- **BasicAuth**: HTTP basic authentication
- **OAuth2Auth**: OAuth2 token flow

**Custom Auth Example**:
```python
class CustomAuth(AuthHandler):
    def apply(self, headers: dict, params: dict) -> None:
        # Add your auth logic
        headers["X-Custom-Auth"] = "value"
```

#### ResponseProcessor (`adapter/runtime/response_processor.py`)
- Parses API responses
- Extracts data based on content type
- Normalizes error messages

---

### Phase 4: MCP Server

**Purpose**: Expose tools to AI agents via the Model Context Protocol.

**Components**:

#### MCPServer (`adapter/server/mcp_server.py`)
- Implements JSON-RPC 2.0 protocol
- Handles stdio transport
- Implements `tools/list` and `tools/call` endpoints
- Integrates with tool registry and executor

**Protocol Flow**:
```
Agent → JSON-RPC Request → MCPServer
    ↓
MCPServer → ToolRegistry (find tool)
    ↓
MCPServer → Executor (execute API call)
    ↓
Executor → REST API
    ↓
API → Response → Executor → MCPServer → Agent
```

---

## Canonical Data Model

All API documentation is normalized to these Pydantic models:

### CanonicalEndpoint

```python
class CanonicalEndpoint(BaseModel):
    name: str                           # snake_case identifier
    method: str                         # GET, POST, PUT, DELETE, etc.
    path: str                           # /users/{user_id}
    description: Optional[str]
    summary: Optional[str]
    parameters: List[CanonicalParameter]
    body_schema: Optional[CanonicalSchema]
    response_schema: Optional[CanonicalSchema]
    tags: List[str]
    security: List[Dict[str, Any]]      # Empty = public endpoint
    deprecated: bool
```

### CanonicalParameter

```python
class CanonicalParameter(BaseModel):
    name: str                           # snake_case
    location: ParameterLocation         # query|path|header|body|cookie
    type: DataType                      # string|number|boolean|object|array
    required: bool
    description: Optional[str]
    default: Optional[Any]
    example: Optional[Any]
```

### CanonicalSchema

```python
class CanonicalSchema(BaseModel):
    type: DataType
    properties: Optional[Dict[str, "CanonicalSchema"]]  # For objects
    items: Optional["CanonicalSchema"]                   # For arrays
    required: Optional[List[str]]
    description: Optional[str]
    example: Optional[Any]
```

---

## Directory Structure

```
adapter/
├── ingestion/              # Phase 1: Loading API docs
│   ├── base_loader.py      # Abstract base class
│   └── loader_openapi.py   # OpenAPI/Swagger loader
├── parsing/                # Phase 1: Normalization
│   ├── canonical_models.py # Pydantic models
│   └── normalizer.py       # Conversion logic
├── mcp/                    # Phase 2: Tool generation
│   ├── tool_generator.py   # Main generator
│   ├── schema_converter.py # Schema conversion
│   └── tool_registry.py    # Tool storage
├── runtime/                # Phase 3: Execution
│   ├── executor.py         # API executor
│   ├── request_builder.py  # Request construction
│   ├── response_processor.py # Response parsing
│   └── auth/               # Authentication handlers
│       ├── auth_handler.py
│       ├── api_key_auth.py
│       ├── bearer_auth.py
│       ├── basic_auth.py
│       └── oauth2_auth.py
├── server/                 # Phase 4: MCP server
│   ├── mcp_server.py       # Main server
│   ├── tool_provider.py    # Tool discovery
│   ├── execution_handler.py # Tool execution
│   └── transport/
│       └── stdio_transport.py # stdio communication
└── pipeline/               # Convenience helpers
    └── ingestion_pipeline.py
```

---

## Design Decisions

### Why No Format Auto-Detection?

**Decision**: Users explicitly call the appropriate loader.

**Rationale**:
- **Simplicity**: Fewer edge cases and failure modes
- **Clarity**: Users know their format
- **Performance**: No overhead from detection logic
- **Maintainability**: Easier to extend

**Example**:
```python
# Explicit (our approach)
from adapter import OpenAPILoader
loader = OpenAPILoader()
spec = loader.load(source)

# vs. Auto-detection (rejected)
from adapter import load_any
spec = load_any(source)  # Magic! But which loader was used?
```

### Why Canonical Data Model?

**Decision**: Normalize all formats to `CanonicalEndpoint`

**Rationale**:
- **Separation of concerns**: Ingestion ≠ Tool generation
- **Extensibility**: Easy to add new input formats
- **Testing**: Each phase can be tested independently
- **Flexibility**: Users can inject custom endpoints

### Why Filter Auth Parameters?

**Decision**: Remove auth params from tool schemas by default

**Rationale**:
- **User experience**: Users shouldn't see internal auth details
- **Security**: Prevents accidental exposure of auth mechanisms
- **Simplicity**: Clean tool interface
- **Flexibility**: Hybrid approach allows customization

### Why Conditional Authentication?

**Decision**: Only apply auth if `endpoint.security` is non-empty

**Rationale**:
- **Correctness**: Public endpoints don't accept auth params
- **Error prevention**: Avoids "too many parameters" errors
- **Standards compliance**: Follows OpenAPI spec

### Why 64-Character Tool Name Limit?

**Decision**: Truncate names intelligently to 64 characters

**Rationale**:
- **MCP requirement**: Claude enforces 64-char limit
- **Intelligent truncation**: Remove version numbers, keep meaningful parts
- **Fallback**: Hard truncate if needed

**Example**:
```python
# Original (73 chars)
binance_delete_sapi_v1_sub_account_sub_account_api_ip_restriction_ip_list

# Truncated (64 chars)
binance_delete_sub_account_sub_account_ip_restriction_ip_list
```

---

## Extension Points

### Adding New Loaders

Extend `BaseLoader` for new formats:

```python
from adapter.ingestion import BaseLoader

class PostmanLoader(BaseLoader):
    def load(self, content: str) -> Dict[str, Any]:
        import json
        collection = json.loads(content)
        # Convert Postman collection to OpenAPI-like structure
        return converted_spec

    def load_from_url(self, url: str) -> Dict[str, Any]:
        response = requests.get(url)
        return self.load(response.text)

    def validate(self, content: str) -> bool:
        try:
            data = json.loads(content)
            return "info" in data and "item" in data
        except:
            return False
```

### Adding New Auth Handlers

Extend `AuthHandler`:

```python
from adapter.runtime import AuthHandler

class MyCustomAuth(AuthHandler):
    def __init__(self, credentials: dict):
        self.credentials = credentials

    def apply(self, headers: dict, params: dict) -> None:
        # Your authentication logic
        headers["Authorization"] = f"Custom {self.credentials['token']}"
```

### Adding New Transports

The MCP server currently uses stdio, but you can add WebSocket:

```python
from adapter.server.transport import BaseTransport

class WebSocketTransport(BaseTransport):
    def send(self, message: str):
        # Send over WebSocket

    def receive(self) -> str:
        # Receive from WebSocket
```

---

## Performance Considerations

### $ref Dereferencing

The OpenAPILoader dereferences all `$ref` pointers during load. For large specs:

- **Time**: O(n) where n = number of refs
- **Space**: O(m) where m = spec size
- **Optimization**: Uses visited set to detect circular refs

### Tool Name Truncation

Truncation is performed once during tool generation:

- **Time**: O(1) per tool
- **Space**: O(1)
- **Caching**: Tool names are cached in the tool object

### Request Execution

Retry logic uses exponential backoff:

- **Default**: 3 retries
- **Backoff**: 2^attempt seconds
- **Timeout**: Configurable per request

---

## Security Considerations

### Authentication

- **Never log credentials**: Auth handlers should not log sensitive data
- **Secure storage**: Use environment variables or encrypted config
- **HTTPS only**: Always use HTTPS for production APIs

### $ref Dereferencing

- **Circular ref protection**: Detects and prevents infinite loops
- **External refs**: Currently not supported (security consideration)

### Input Validation

- **Pydantic models**: All inputs validated via Pydantic
- **Type safety**: Strong typing throughout
- **Error handling**: Comprehensive validation errors

---

## Testing Strategy

### Unit Tests

Each component has isolated tests:

```python
# Test loader
def test_openapi_loader():
    loader = OpenAPILoader()
    spec = loader.load(sample_yaml)
    assert spec["openapi"] == "3.0.0"

# Test normalizer
def test_normalizer():
    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)
    assert len(endpoints) > 0

# Test tool generator
def test_tool_generator():
    generator = ToolGenerator()
    tools = generator.generate_tools(endpoints)
    assert all(len(t.name) <= 64 for t in tools)
```

### Integration Tests

Test the complete pipeline:

```python
def test_full_pipeline():
    # Load → Normalize → Generate → Execute
    loader = OpenAPILoader()
    spec = loader.load("api.yaml")

    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)

    generator = ToolGenerator()
    tools = generator.generate_tools(endpoints)

    executor = APIExecutor(base_url="https://api.test", auth=NoAuth())
    result = executor.execute(endpoints[0], arguments={})

    assert result.success
```

---

## Future Enhancements

### Planned

- **Postman Loader**: Parse Postman collections
- **GraphQL Loader**: Parse GraphQL schemas
- **WebSocket Transport**: For MCP server
- **Caching Layer**: Cache responses and tools
- **Async Execution**: Support async/await

### Under Consideration

- **Rate Limiting**: Built-in rate limit handling
- **Metrics**: Execution metrics and monitoring
- **Pagination**: Automatic pagination support
- **Batch Execution**: Execute multiple tools in parallel

---

## Contributing to Architecture

When proposing architectural changes:

1. **Maintain phase separation**: Keep phases independent
2. **Preserve extensibility**: Use interfaces/base classes
3. **Document decisions**: Update this file
4. **Add tests**: Ensure backward compatibility
5. **Consider performance**: Profile if adding complexity

---

**For questions or discussions**: [GitHub Discussions](https://github.com/your-username/rest-to-mcp-adapter/discussions)
