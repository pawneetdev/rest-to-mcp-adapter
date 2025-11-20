#!/usr/bin/env python3
"""
Test script for authentication parameter filtering.

Demonstrates the hybrid auth filtering approach:
1. Default common auth params
2. Auto-detected params from OpenAPI security schemes
3. Custom user overrides
"""

import json
from adapter import OpenAPILoader, Normalizer, ToolGenerator


def test_default_auth_params():
    """Test 1: Default auth parameters filtering"""
    print("=" * 70)
    print("Test 1: Default Auth Parameters")
    print("=" * 70)

    # Create a simple OpenAPI spec with common auth params
    spec_content = """
openapi: 3.0.0
info:
  title: Test API
  version: 1.0.0
paths:
  /account:
    get:
      summary: Get account info
      parameters:
        - name: timestamp
          in: query
          required: true
          schema:
            type: integer
        - name: signature
          in: query
          required: true
          schema:
            type: string
        - name: symbol
          in: query
          required: false
          schema:
            type: string
      responses:
        '200':
          description: Success
"""

    loader = OpenAPILoader()
    spec = loader.load(spec_content)

    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)

    # Generate tools with default auth params
    generator = ToolGenerator()
    tools = generator.generate_tools(endpoints)

    tool = tools[0]
    print(f"Tool name: {tool.name}")
    print(f"Parameters in endpoint: timestamp, signature, symbol")
    print(f"Parameters in tool schema: {list(tool.inputSchema.get('properties', {}).keys())}")
    print(f"Auth params filtered: {generator.auth_params}")

    # Verify signature and timestamp are filtered
    props = tool.inputSchema.get('properties', {})
    assert 'timestamp' not in props, "timestamp should be filtered"
    assert 'signature' not in props, "signature should be filtered"
    assert 'symbol' in props, "symbol should NOT be filtered"

    print("✓ Test passed: timestamp and signature filtered by defaults\n")


def test_auto_detected_auth_params():
    """Test 2: Auto-detected auth params from security schemes"""
    print("=" * 70)
    print("Test 2: Auto-Detected Auth Parameters")
    print("=" * 70)

    spec_content = """
openapi: 3.0.0
info:
  title: API with Security Schemes
  version: 1.0.0
components:
  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: X-API-KEY
    SignatureAuth:
      type: apiKey
      in: query
      name: sig
paths:
  /data:
    get:
      summary: Get data
      parameters:
        - name: X-API-KEY
          in: header
          required: true
          schema:
            type: string
        - name: sig
          in: query
          required: true
          schema:
            type: string
        - name: limit
          in: query
          required: false
          schema:
            type: integer
      responses:
        '200':
          description: Success
"""

    loader = OpenAPILoader()
    spec = loader.load(spec_content)

    # Extract auth params from security schemes
    auto_detected = loader.extract_auth_parameters(spec)
    print(f"Auto-detected auth params: {auto_detected}")

    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)

    # Generate tools with auto-detected params
    generator = ToolGenerator(auto_detected_auth_params=auto_detected)
    tools = generator.generate_tools(endpoints)

    tool = tools[0]
    print(f"Tool name: {tool.name}")
    print(f"Parameters in endpoint: X-API-KEY, sig, limit")
    print(f"Parameters in tool schema: {list(tool.inputSchema.get('properties', {}).keys())}")
    print(f"Auth params filtered: {generator.auth_params}")

    # Verify X-API-KEY and sig are filtered
    # Note: X-API-KEY becomes x_api_key after normalization (hyphens -> underscores)
    props = tool.inputSchema.get('properties', {})
    assert 'x_api_key' not in props, "x_api_key should be filtered"
    assert 'sig' not in props, "sig should be filtered"
    assert 'limit' in props, "limit should NOT be filtered"

    print("✓ Test passed: Auto-detected params filtered\n")


def test_custom_override_auth_params():
    """Test 3: Custom override auth params"""
    print("=" * 70)
    print("Test 3: Custom Override Auth Parameters")
    print("=" * 70)

    spec_content = """
openapi: 3.0.0
info:
  title: Custom Auth API
  version: 1.0.0
paths:
  /resource:
    get:
      summary: Get resource
      parameters:
        - name: custom_auth_token
          in: header
          required: true
          schema:
            type: string
        - name: custom_nonce
          in: query
          required: true
          schema:
            type: string
        - name: timestamp
          in: query
          required: true
          schema:
            type: integer
        - name: user_id
          in: query
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Success
"""

    loader = OpenAPILoader()
    spec = loader.load(spec_content)

    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)

    # Generate tools with custom auth params only
    # This overrides defaults, so 'timestamp' will NOT be filtered
    custom_auth = {'custom_auth_token', 'custom_nonce'}
    generator = ToolGenerator(auth_params=custom_auth)
    tools = generator.generate_tools(endpoints)

    tool = tools[0]
    print(f"Tool name: {tool.name}")
    print(f"Parameters in endpoint: custom_auth_token, custom_nonce, timestamp, user_id")
    print(f"Parameters in tool schema: {list(tool.inputSchema.get('properties', {}).keys())}")
    print(f"Auth params filtered: {generator.auth_params}")

    # Verify only custom params are filtered
    props = tool.inputSchema.get('properties', {})
    assert 'custom_auth_token' not in props, "custom_auth_token should be filtered"
    assert 'custom_nonce' not in props, "custom_nonce should be filtered"
    assert 'timestamp' in props, "timestamp should NOT be filtered (custom override)"
    assert 'user_id' in props, "user_id should NOT be filtered"

    print("✓ Test passed: Only custom params filtered\n")


def test_hybrid_approach():
    """Test 4: Hybrid - defaults + auto-detected"""
    print("=" * 70)
    print("Test 4: Hybrid Approach (Defaults + Auto-Detected)")
    print("=" * 70)

    spec_content = """
openapi: 3.0.0
info:
  title: Hybrid Auth API
  version: 1.0.0
components:
  securitySchemes:
    CustomAuth:
      type: apiKey
      in: header
      name: X-Custom-Token
paths:
  /hybrid:
    get:
      summary: Hybrid endpoint
      parameters:
        - name: timestamp
          in: query
          schema:
            type: integer
        - name: signature
          in: query
          schema:
            type: string
        - name: X-Custom-Token
          in: header
          schema:
            type: string
        - name: page
          in: query
          schema:
            type: integer
      responses:
        '200':
          description: Success
"""

    loader = OpenAPILoader()
    spec = loader.load(spec_content)

    # Extract auto-detected params
    auto_detected = loader.extract_auth_parameters(spec)
    print(f"Auto-detected params: {auto_detected}")

    normalizer = Normalizer()
    endpoints = normalizer.normalize_openapi(spec)

    # Generate tools with defaults + auto-detected
    generator = ToolGenerator(auto_detected_auth_params=auto_detected)
    tools = generator.generate_tools(endpoints)

    tool = tools[0]
    print(f"Tool name: {tool.name}")
    print(f"Parameters in endpoint: timestamp, signature, X-Custom-Token, page")
    print(f"Parameters in tool schema: {list(tool.inputSchema.get('properties', {}).keys())}")
    print(f"Total auth params filtered: {len(generator.auth_params)}")

    # Verify all auth params are filtered
    # Note: X-Custom-Token becomes x_custom_token after normalization
    props = tool.inputSchema.get('properties', {})
    assert 'timestamp' not in props, "timestamp should be filtered (default)"
    assert 'signature' not in props, "signature should be filtered (default)"
    assert 'x_custom_token' not in props, "x_custom_token should be filtered (auto-detected)"
    assert 'page' in props, "page should NOT be filtered"

    print("✓ Test passed: Both defaults and auto-detected params filtered\n")


def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("Authentication Parameter Filtering Test Suite")
    print("=" * 70 + "\n")

    try:
        test_default_auth_params()
        test_auto_detected_auth_params()
        test_custom_override_auth_params()
        test_hybrid_approach()

        print("=" * 70)
        print("✓ All tests passed!")
        print("=" * 70)

    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
