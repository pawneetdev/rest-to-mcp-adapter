#!/usr/bin/env python3
"""
Debug script to investigate empty parameter names in Binance OpenAPI spec
"""

import json
import yaml
import requests
from pprint import pprint

# Load the raw spec
url = "https://raw.githubusercontent.com/binance/binance-api-swagger/refs/heads/master/spot_api.yaml"
response = requests.get(url)
raw_spec = yaml.safe_load(response.text)

print("=" * 70)
print("INVESTIGATING BINANCE OPENAPI SPEC")
print("=" * 70)

# Check raw spec for empty parameter names
print("\n[1] Checking raw YAML for empty parameter names...")
found_empty = False

for path, path_item in raw_spec.get('paths', {}).items():
    for method in ['get', 'post', 'put', 'delete', 'patch']:
        if method not in path_item:
            continue

        operation = path_item[method]
        if 'parameters' not in operation:
            continue

        for i, param in enumerate(operation['parameters']):
            # Check if it's a $ref
            if '$ref' in param:
                print(f"  Found $ref in {method.upper()} {path}: {param['$ref']}")
                continue

            # Check for empty name
            param_name = param.get('name', '')
            if not param_name or not param_name.strip():
                found_empty = True
                print(f"\n  ❌ FOUND EMPTY PARAMETER!")
                print(f"     Path: {method.upper()} {path}")
                print(f"     Index: {i}")
                print(f"     Parameter: {param}")

if not found_empty:
    print("  ✓ No empty parameter names in raw YAML")

# Now check what LangChain does to it
print("\n[2] Checking after LangChain processing...")
try:
    from langchain_community.utilities.openapi import OpenAPISpec

    openapi_spec = OpenAPISpec.from_spec_dict(raw_spec)
    processed_spec = openapi_spec.spec_dict

    print("  ✓ LangChain processed the spec")

    # Check processed spec for empty names
    found_empty_after = False

    for path, path_item in processed_spec.get('paths', {}).items():
        for method in ['get', 'post', 'put', 'delete', 'patch']:
            if method not in path_item:
                continue

            operation = path_item[method]
            if 'parameters' not in operation:
                continue

            for i, param in enumerate(operation['parameters']):
                param_name = param.get('name', '')
                if not param_name or not param_name.strip():
                    found_empty_after = True
                    print(f"\n  ❌ EMPTY PARAMETER AFTER LANGCHAIN!")
                    print(f"     Path: {method.upper()} {path}")
                    print(f"     Index: {i}")
                    print(f"     Parameter keys: {list(param.keys())}")
                    print(f"     Parameter: {param}")

                    # Show the raw version too
                    raw_param = raw_spec['paths'][path][method]['parameters'][i]
                    print(f"     Raw param: {raw_param}")

    if not found_empty_after:
        print("  ✓ No empty parameter names after LangChain")

    # Save processed spec for inspection
    with open('/tmp/binance_processed.json', 'w') as f:
        json.dump(processed_spec, f, indent=2)
    print("\n  Saved processed spec to: /tmp/binance_processed.json")

except ImportError:
    print("  ⚠ LangChain not available")
except Exception as e:
    print(f"  ❌ Error processing with LangChain: {e}")
    import traceback
    traceback.print_exc()

# Now check with our loader
print("\n[3] Checking with our OpenAPILoader...")
try:
    from adapter.ingestion import OpenAPILoader

    loader = OpenAPILoader()
    spec = loader.load(url)

    print("  ✓ Our loader processed the spec")

    # Check for empty names
    found_empty_ours = False

    for path, path_item in spec.get('paths', {}).items():
        for method in ['get', 'post', 'put', 'delete', 'patch']:
            if method not in path_item:
                continue

            operation = path_item[method]
            if 'parameters' not in operation:
                continue

            for i, param in enumerate(operation['parameters']):
                param_name = param.get('name', '')
                if not param_name or not param_name.strip():
                    found_empty_ours = True
                    print(f"\n  ❌ EMPTY PARAMETER IN OUR LOADER!")
                    print(f"     Path: {method.upper()} {path}")
                    print(f"     Index: {i}")
                    print(f"     Parameter: {param}")

    if not found_empty_ours:
        print("  ✓ No empty parameter names from our loader")

    # Save our processed spec
    with open('/tmp/binance_our_loader.json', 'w') as f:
        json.dump(spec, f, indent=2)
    print("  Saved our loader output to: /tmp/binance_our_loader.json")

except Exception as e:
    print(f"  ❌ Error with our loader: {e}")
    import traceback
    traceback.print_exc()

# Check a specific endpoint in detail
print("\n[4] Detailed check of a specific endpoint...")
print("  Checking: GET /api/v3/ticker/24hr")

try:
    endpoint_path = '/api/v3/ticker/24hr'
    if endpoint_path in raw_spec.get('paths', {}):
        endpoint = raw_spec['paths'][endpoint_path]['get']

        print(f"\n  Raw parameters ({len(endpoint.get('parameters', []))}):")
        for i, param in enumerate(endpoint.get('parameters', [])):
            if '$ref' in param:
                print(f"    {i}: $ref -> {param['$ref']}")
            else:
                print(f"    {i}: name='{param.get('name', '')}', in={param.get('in', '')}")

        # Check what LangChain resolves this to
        if 'openapi_spec' in locals():
            processed_endpoint = processed_spec['paths'][endpoint_path]['get']
            print(f"\n  After LangChain ({len(processed_endpoint.get('parameters', []))}):")
            for i, param in enumerate(processed_endpoint.get('parameters', [])):
                print(f"    {i}: name='{param.get('name', '')}', in={param.get('in', '')}")
                if not param.get('name', '').strip():
                    print(f"       ❌ EMPTY NAME! Full param: {param}")
except Exception as e:
    print(f"  Error checking endpoint: {e}")

print("\n" + "=" * 70)
print("INVESTIGATION COMPLETE")
print("=" * 70)
