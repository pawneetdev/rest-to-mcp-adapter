# Phase 3: Runtime Execution - Quick Start Guide

## What is Phase 3?

Phase 3 allows you to **execute actual REST API calls** using the canonical endpoints you've loaded and normalized.

## Basic Flow

```
OpenAPI Spec → Normalize → Generate Tools → EXECUTE API CALLS ✨
```

## Step-by-Step Guide

### Step 1: Set Up Authentication

First, import the authentication classes:

```python
from adapter.runtime import (
    APIExecutor,      # Main executor
    NoAuth,           # No authentication
    APIKeyAuth,       # API key authentication
    BearerAuth,       # Bearer token authentication
    BasicAuth,        # HTTP Basic auth
)
```

Choose your authentication method:

```python
# Option A: No authentication (public APIs)
auth = NoAuth()

# Option B: API Key in header
auth = APIKeyAuth(
    key="your-api-key-here",
    location="header",
    name="X-API-Key"  # or "Authorization", depending on API
)

# Option C: API Key in query parameter
auth = APIKeyAuth(
    key="your-api-key-here",
    location="query",
    name="api_key"  # parameter name
)

# Option D: Bearer Token
auth = BearerAuth(token="your-bearer-token")

# Option E: Basic Authentication (username:password)
auth = BasicAuth(
    username="your-username",
    password="your-password"
)
```

### Step 2: Create the API Executor

```python
executor = APIExecutor(
    base_url="https://api.example.com",  # Base URL of the API
    auth=auth,                            # Authentication from Step 1
    max_retries=3,                        # Retry failed requests 3 times
    retry_backoff=1.0,                    # Start with 1s, doubles each retry
    timeout=30,                           # Request timeout in seconds
)
```

### Step 3: Execute an API Call

```python
# You already have endpoints from Phase 1:
# endpoints = normalizer.normalize_openapi(spec)

# Choose an endpoint to call
my_endpoint = endpoints[0]  # or find specific endpoint

# Prepare parameters
parameters = {
    "user_id": "123",           # Path parameter
    "include": "profile",       # Query parameter
    "X-Request-ID": "abc-123",  # Header parameter
    "name": "John Doe",         # Body parameter
}

# Execute the API call
result = executor.execute(
    endpoint=my_endpoint,
    parameters=parameters
)
```

### Step 4: Handle the Response

```python
if result.success:
    # ✅ Success!
    print(f"Status Code: {result.response.status_code}")
    print(f"Execution Time: {result.execution_time_ms}ms")
    print(f"Attempts: {result.attempts}")
    print(f"Data: {result.response.data}")

    # Access response data
    data = result.response.data  # Already parsed JSON

else:
    # ❌ Failed
    print(f"Error: {result.response.error}")
    print(f"Status Code: {result.response.status_code}")
    print(f"Attempts Made: {result.attempts}")
```

## Complete Example

Here's a complete working example:

```python
from adapter.ingestion import OpenAPILoader
from adapter.parsing import Normalizer
from adapter.runtime import APIExecutor, BearerAuth

# Load and normalize OpenAPI spec
loader = OpenAPILoader()
spec = loader.load("https://api.example.com/openapi.json")

normalizer = Normalizer()
endpoints = normalizer.normalize_openapi(spec)

# Set up authentication
auth = BearerAuth(token="your-token-here")

# Create executor
executor = APIExecutor(
    base_url="https://api.example.com",
    auth=auth,
    max_retries=3,
    timeout=30
)

# Find the endpoint you want
get_user_endpoint = None
for endpoint in endpoints:
    if endpoint.name == "get_user_by_id":
        get_user_endpoint = endpoint
        break

# Execute the API call
result = executor.execute(
    endpoint=get_user_endpoint,
    parameters={"user_id": "123"}
)

# Handle response
if result.success:
    user_data = result.response.data
    print(f"User: {user_data}")
else:
    print(f"Error: {result.response.error}")
```

## Understanding the Result Object

The `ExecutionResult` object contains:

```python
result.success                  # bool: True if successful
result.endpoint_name            # str: Name of endpoint called
result.execution_time_ms        # float: Execution time in milliseconds
result.attempts                 # int: Number of attempts made

result.response.status_code     # int: HTTP status code (200, 404, etc.)
result.response.data            # Any: Parsed response data (JSON → dict/list)
result.response.error           # str: Error message if failed
result.response.raw_text        # str: Raw response text
result.response.headers         # dict: Response headers
```

## Common Patterns

### Pattern 1: Find and Execute Specific Endpoint

```python
# Find endpoint by name
target_endpoint = None
for ep in endpoints:
    if "create_user" in ep.name:
        target_endpoint = ep
        break

if target_endpoint:
    result = executor.execute(
        endpoint=target_endpoint,
        parameters={
            "email": "user@example.com",
            "name": "John Doe"
        }
    )
```

### Pattern 2: Handle Required vs Optional Parameters

```python
# Build parameters based on endpoint requirements
parameters = {}

for param in my_endpoint.parameters:
    if param.required:
        # Must provide required parameters
        parameters[param.name] = get_user_input(param.name)
    else:
        # Optional parameters can be omitted
        if should_include_optional:
            parameters[param.name] = optional_value
```

### Pattern 3: Batch Execute Multiple Calls

```python
results = []

for endpoint in endpoints[:5]:  # First 5 endpoints
    result = executor.execute(
        endpoint=endpoint,
        parameters={}  # Adjust per endpoint
    )
    results.append(result)

# Summary
successful = [r for r in results if r.success]
failed = [r for r in results if not r.success]

print(f"Successful: {len(successful)}/{len(results)}")
```

### Pattern 4: Retry Configuration for Different APIs

```python
# For rate-limited APIs (e.g., Twitter, GitHub)
executor = APIExecutor(
    base_url="https://api.example.com",
    auth=auth,
    max_retries=5,                          # More retries
    retry_backoff=2.0,                      # Longer backoff
    retry_on_status_codes=[429, 500, 502, 503, 504],  # Include 429 (rate limit)
    timeout=60,                             # Longer timeout
)

# For fast, reliable APIs
executor = APIExecutor(
    base_url="https://api.example.com",
    auth=auth,
    max_retries=2,                          # Fewer retries
    retry_backoff=0.5,                      # Shorter backoff
    timeout=10,                             # Shorter timeout
)
```

## What Gets Handled Automatically

✅ **Path parameter substitution**: `/users/{user_id}` → `/users/123`

✅ **Query parameter encoding**: Special characters, arrays, etc.

✅ **Header construction**: Authentication, custom headers

✅ **Request body formatting**: Automatic JSON serialization

✅ **Response parsing**: Automatic JSON parsing

✅ **Retry logic**: Exponential backoff for transient failures

✅ **Error handling**: Detailed error messages

## Important Notes

1. **Base URL**: The `base_url` in `APIExecutor` gets prepended to all endpoint paths
   ```python
   base_url="https://api.example.com"
   endpoint.path="/users/123"
   # → Final URL: https://api.example.com/users/123
   ```

2. **Authentication**: Applied automatically to every request

3. **Parameters**: Automatically routed to correct location (path/query/header/body)

4. **Retries**: Only happen for specific status codes (429, 500, 502, 503, 504) by default

5. **Timeouts**: If a request takes longer than `timeout` seconds, it fails and may retry

## Troubleshooting

### "Missing required parameter"
Check what parameters the endpoint needs:
```python
for param in endpoint.parameters:
    if param.required:
        print(f"Required: {param.name} ({param.location.value})")
```

### "Authentication failed (401)"
- Verify your API credentials are correct
- Check if you're using the right auth method (APIKey vs Bearer vs Basic)
- Check the location (header vs query) for API keys

### "Request timeout"
- Increase `timeout` parameter in `APIExecutor`
- Check if the API endpoint is slow or down

### "Max retries reached"
- Check if the API is having issues
- Verify your request parameters are correct
- Try with `max_retries=0` to disable retries for debugging

## Next Steps

1. **Try it yourself**: Use `test_dataforseo.py` as a template
2. **Add your credentials**: Replace placeholder auth with real credentials
3. **Execute real calls**: Uncomment the execution code
4. **Handle responses**: Process the `result.response.data` for your use case

## More Examples

See `examples/phase3_runtime_execution.py` for 6 comprehensive examples covering all features.
