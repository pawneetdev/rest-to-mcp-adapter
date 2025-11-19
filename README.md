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

## 🚀 Phase 1: Ingestion & Normalization (Current)

This initial release provides the **foundation layer**:

- **OpenAPI Loader**: Parse OpenAPI 3.x and Swagger 2.x from URLs, files, or raw content
- **HTML Loader**: Extract clean text from HTML docs (URLs or raw HTML)
- **Canonical Models**: Pydantic-based unified data model
- **Normalizer**: Convert raw data to canonical endpoint format
- **LangChain Integration**: Optional integration for enhanced parsing

### What's NOT in Phase 1

- ❌ MCP tool generation (future phase)
- ❌ Runtime REST execution engine (future phase)
- ❌ LLM-based HTML/PDF parsing (future phase)
- ❌ Recursive HTML crawling (future phase)
- ❌ Postman/GraphQL loaders (future phase)

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

### Phase 1: Ingestion & Normalization ✅ (Current)
- Direct loader calls (no format detection)
- OpenAPI/HTML loaders with URL/file support
- Canonical models
- Normalization pipeline

### Phase 2: LLM-Based Extraction (Next)
- HTML → structured endpoints (via LLM)
- PDF → structured endpoints (via LLM)
- Markdown → structured endpoints (via LLM)
- Unstructured docs → structured endpoints

### Phase 3: MCP Tool Generation
- Generate MCP tool definitions from canonical endpoints
- Tool metadata generation
- Parameter validation schemas

### Phase 4: Runtime Execution Engine
- REST API call execution
- Authentication handling
- Response processing
- Error handling

### Phase 5: Agent-Facing MCP Server
- Complete MCP server implementation
- WebSocket/stdio transport
- Tool discovery and execution
- Integration with Claude/LLMs

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

Contributions are welcome! This is Phase 1 of a larger vision.

Areas for contribution:
- Additional loaders (Postman, GraphQL, etc.)
- Recursive HTML crawling implementation
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
