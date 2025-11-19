# Universal REST → MCP Adapter

A production-quality framework for converting **any** REST API documentation into **MCP-compatible tools** for Large Language Models and agent systems.

## 🎯 Project Vision

This system transforms diverse API documentation formats (OpenAPI, HTML, Postman, GraphQL, PDF, etc.) into a unified canonical format that can be used to generate MCP tools for LLM-powered agents.

### Supported Formats (Planned)

| Format | Phase 1 | Future Phases |
|--------|---------|---------------|
| OpenAPI/Swagger (JSON/YAML) | ✅ | - |
| HTML Documentation | ✅ | LLM extraction |
| Postman Collections | - | ✅ |
| GraphQL Schemas | - | ✅ |
| Markdown Documentation | - | ✅ |
| PDF Documentation | - | ✅ |

## 🚀 Phase 1: Ingestion & Normalization (Current)

This initial release provides the **foundation layer**:

- **Format Detection**: Automatically identify API documentation formats
- **Loader Framework**: Extensible loader architecture with LangChain integration
- **OpenAPI Loader**: Parse and validate OpenAPI 3.x and Swagger 2.x specs
- **HTML Loader**: Extract clean text from HTML documentation
- **Canonical Models**: Pydantic-based unified data model
- **Normalizer**: Convert raw data to canonical endpoint format
- **Ingestion Pipeline**: Orchestrated end-to-end ingestion

### What's NOT in Phase 1

- ❌ MCP tool generation (future phase)
- ❌ Runtime REST execution engine (future phase)
- ❌ LLM-based HTML/PDF parsing (future phase)
- ❌ Postman/GraphQL loaders (future phase)

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/pawneetdev/rest-to-mcp-adapter.git
cd rest-to-mcp-adapter

# Install dependencies
pip install -r requirements.txt
```

### Dependencies

- **pydantic** ≥2.0.0 - Data validation and canonical models
- **PyYAML** ≥6.0 - YAML parsing
- **beautifulsoup4** ≥4.12.0 - HTML parsing
- **langchain-community** ≥0.0.20 - LangChain integration (optional)

## 🏗️ Architecture

```
adapter/
├── ingestion/          # Format detection and loading
│   ├── detector.py     # Automatic format detection
│   ├── base_loader.py  # Abstract loader interface
│   ├── loader_openapi.py  # OpenAPI/Swagger loader
│   └── loader_html.py     # HTML documentation loader
├── parsing/            # Normalization and canonical models
│   ├── canonical_models.py  # Pydantic models
│   └── normalizer.py        # Data normalization
└── pipeline/           # Orchestration
    └── ingestion_pipeline.py  # End-to-end pipeline
```

### Key Design Principles

1. **Extensibility**: Easy to add new loaders for additional formats
2. **LangChain Integration**: Leverage existing utilities where available
3. **Resilience**: Graceful handling of partial/malformed specs
4. **Type Safety**: Pydantic models for validation
5. **Separation of Concerns**: Clear boundaries between detection, loading, and normalization

## 📚 Usage

### Quick Start

```python
from adapter.pipeline import ingest_api_source
from adapter.parsing import Normalizer

# Ingest an OpenAPI specification
result = ingest_api_source(
    source="petstore.yaml",
    raw_content=open("petstore.yaml").read()
)

if result.success:
    # Normalize to canonical format
    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(result.loaded_data)

    for endpoint in endpoints:
        print(f"{endpoint.name}: {endpoint.method} {endpoint.path}")
```

### Example 1: OpenAPI Ingestion

```python
from adapter.pipeline import ingest_api_source
from adapter.parsing import Normalizer

openapi_yaml = """
openapi: 3.0.0
info:
  title: Sample API
  version: 1.0.0
paths:
  /users/{userId}:
    get:
      summary: Get user by ID
      parameters:
        - name: userId
          in: path
          required: true
          schema:
            type: integer
      responses:
        '200':
          description: User object
"""

# Ingest and normalize
result = ingest_api_source("api.yaml", openapi_yaml)
normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(result.loaded_data)

# Access canonical endpoint data
endpoint = endpoints[0]
print(f"Name: {endpoint.name}")           # get_users_by_user_id
print(f"Method: {endpoint.method}")       # GET
print(f"Path: {endpoint.path}")           # /users/{userId}
print(f"Parameters: {len(endpoint.parameters)}")  # 1
```

### Example 2: HTML Documentation

```python
from adapter.pipeline import ingest_api_source

html_content = """
<html>
<head><title>API Docs</title></head>
<body>
    <h1>GET /api/products</h1>
    <p>Retrieve all products.</p>

    <h2>Query Parameters</h2>
    <ul>
        <li>category (string): Filter by category</li>
        <li>limit (integer): Max results</li>
    </ul>
</body>
</html>
"""

result = ingest_api_source("docs.html", html_content)

if result.success:
    # Clean text ready for LLM extraction (Phase 2)
    clean_text = result.loaded_data
    print(clean_text)
```

### Example 3: Format Detection

```python
from adapter.pipeline import ingest_api_source

# Automatic detection
samples = {
    "openapi.json": '{"openapi": "3.0.0", "info": {}}',
    "swagger.yaml": "swagger: '2.0'\ninfo:\n  title: API",
    "docs.html": "<html><body>API Documentation</body></html>",
}

for filename, content in samples.items():
    result = ingest_api_source(filename, content)
    print(f"{filename} -> {result.format}")
```

### Example 4: Custom Configuration

```python
from adapter.pipeline import ingest_api_source

# Strict validation
result = ingest_api_source(
    source="spec.yaml",
    raw_content=content,
    strict=True,  # Enforce strict OpenAPI validation
)

# Without LangChain (use manual parsing)
result = ingest_api_source(
    source="spec.yaml",
    raw_content=content,
    use_langchain=False,
)
```

### Complete Examples

See `examples/basic_usage.py` for comprehensive usage examples:

```bash
python examples/basic_usage.py
```

## 🔌 Extensibility

### Adding Custom Loaders

The framework is designed for easy extension:

```python
from adapter.ingestion.base_loader import BaseLoader
from adapter.pipeline.ingestion_pipeline import IngestionPipeline
from adapter.ingestion.detector import APIFormat

# Define custom loader
class PostmanLoader(BaseLoader):
    def load(self, content: str) -> dict:
        import json
        return json.loads(content)

# Register with pipeline
pipeline = IngestionPipeline()
# pipeline.register_loader(APIFormat.POSTMAN, PostmanLoader)
```

### Future Loader Support

The architecture is ready for:
- **Postman Collections**: Import Postman collection JSON
- **GraphQL Schemas**: Parse GraphQL schema definitions
- **Markdown Docs**: Extract endpoints from Markdown
- **PDF Docs**: Extract text and parse with LLM

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

### Phase 1: Ingestion & Normalization ✅ (Current)
- Format detection
- OpenAPI/HTML loaders
- Canonical models
- Normalization pipeline

### Phase 2: Extended Loaders (Next)
- Postman collection loader
- GraphQL schema loader
- Markdown documentation loader
- PDF documentation loader (with LLM extraction)

### Phase 3: LLM-Based Extraction
- HTML → structured endpoints (via LLM)
- PDF → structured endpoints (via LLM)
- Markdown → structured endpoints (via LLM)
- Unstructured docs → structured endpoints

### Phase 4: MCP Tool Generation
- Generate MCP tool definitions from canonical endpoints
- Tool metadata generation
- Parameter validation schemas

### Phase 5: Runtime Execution Engine
- REST API call execution
- Authentication handling
- Response processing
- Error handling

### Phase 6: Agent-Facing MCP Server
- Complete MCP server implementation
- WebSocket/stdio transport
- Tool discovery and execution
- Integration with Claude/LLMs

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions are welcome! This is Phase 1 of a larger vision.

Areas for contribution:
- Additional loaders (Postman, GraphQL, etc.)
- Enhanced normalization logic
- Better error handling
- Documentation improvements
- Test coverage

## 📞 Support

For issues and questions:
- GitHub Issues: [Issues](https://github.com/pawneetdev/rest-to-mcp-adapter/issues)
- Discussions: [Discussions](https://github.com/pawneetdev/rest-to-mcp-adapter/discussions)

---

**Built with** ❤️ **for the LLM agent ecosystem**
