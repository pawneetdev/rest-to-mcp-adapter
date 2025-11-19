"""
Test script for MCP server.

This script demonstrates how to interact with an MCP server by sending
JSON-RPC messages. It can be used to test the server without needing
a full MCP client.

Usage:
    python test_mcp_server.py

This will send a series of test messages to the MCP server and display
the responses.
"""

import json
import subprocess
import sys


def send_message(process, message):
    """
    Send a JSON-RPC message to the MCP server.

    Args:
        process: Subprocess running the MCP server
        message: Dictionary to send as JSON

    Returns:
        Response dictionary
    """
    # Convert to JSON and send
    json_str = json.dumps(message) + "\n"
    process.stdin.write(json_str)
    process.stdin.flush()

    # Read response
    response_line = process.stdout.readline()
    if not response_line:
        raise Exception("No response from server")

    return json.loads(response_line)


def test_initialize(process):
    """Test the initialize method."""
    print("\n" + "=" * 70)
    print("TEST 1: Initialize")
    print("=" * 70)

    message = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }

    print("\nSending:", json.dumps(message, indent=2))

    response = send_message(process, message)

    print("\nReceived:", json.dumps(response, indent=2))

    if "result" in response:
        print("\n✓ Initialize successful")
        print(f"  Server: {response['result']['serverInfo']['name']}")
        print(f"  Version: {response['result']['serverInfo']['version']}")
    else:
        print("\n✗ Initialize failed")

    return response


def test_tools_list(process):
    """Test the tools/list method."""
    print("\n" + "=" * 70)
    print("TEST 2: List Tools")
    print("=" * 70)

    message = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }

    print("\nSending:", json.dumps(message, indent=2))

    response = send_message(process, message)

    print("\nReceived response with", len(str(response)), "characters")

    if "result" in response and "tools" in response["result"]:
        tools = response["result"]["tools"]
        print(f"\n✓ Tools list successful")
        print(f"  Total tools: {len(tools)}")

        # Show first few tools
        print("\n  First 3 tools:")
        for i, tool in enumerate(tools[:3]):
            print(f"\n  Tool {i+1}:")
            print(f"    Name: {tool['name']}")
            print(f"    Description: {tool['description'][:60]}...")
            if 'inputSchema' in tool and 'properties' in tool['inputSchema']:
                params = list(tool['inputSchema']['properties'].keys())
                print(f"    Parameters: {params[:5]}")
    else:
        print("\n✗ Tools list failed")

    return response


def test_tools_call(process, tool_name, arguments):
    """Test the tools/call method."""
    print("\n" + "=" * 70)
    print(f"TEST 3: Call Tool '{tool_name}'")
    print("=" * 70)

    message = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        }
    }

    print("\nSending:", json.dumps(message, indent=2))

    response = send_message(process, message)

    print("\nReceived response:")

    if "result" in response:
        result = response["result"]
        print(f"  isError: {result.get('isError', False)}")

        if "content" in result:
            for item in result["content"]:
                if item["type"] == "text":
                    text = item["text"]
                    # Truncate long responses
                    if len(text) > 500:
                        print(f"  Content (truncated):\n{text[:500]}...")
                    else:
                        print(f"  Content:\n{text}")

        if not result.get('isError', False):
            print("\n✓ Tool call successful")
        else:
            print("\n✗ Tool call returned error")
    else:
        print("\n✗ Tool call failed")
        print(json.dumps(response, indent=2))

    return response


def main():
    """Run all tests."""
    print("=" * 70)
    print("MCP Server Test Suite")
    print("=" * 70)
    print("\nThis script will:")
    print("  1. Start the MCP server")
    print("  2. Send test JSON-RPC messages")
    print("  3. Display the responses")
    print("\nMake sure you have a configured server in phase4_mcp_server.py")
    print("=" * 70)

    # Start the MCP server as a subprocess
    print("\nStarting MCP server...")

    try:
        process = subprocess.Popen(
            [sys.executable, "examples/phase4_mcp_server.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        print("✓ MCP server started (PID:", process.pid, ")")

        # Run tests
        try:
            # Test 1: Initialize
            init_response = test_initialize(process)

            # Test 2: List tools
            list_response = test_tools_list(process)

            # Test 3: Call a tool (if we have tools)
            if "result" in list_response and "tools" in list_response["result"]:
                tools = list_response["result"]["tools"]

                if tools:
                    # Find a simple GET endpoint to test
                    test_tool = None
                    for tool in tools:
                        # Look for a tool with no required parameters
                        if 'inputSchema' in tool:
                            required = tool['inputSchema'].get('required', [])
                            if not required:
                                test_tool = tool
                                break

                    if test_tool:
                        test_tools_call(
                            process,
                            tool_name=test_tool['name'],
                            arguments={}
                        )
                    else:
                        print("\n" + "=" * 70)
                        print("TEST 3: Skipped (no tools without required params)")
                        print("=" * 70)
                else:
                    print("\n" + "=" * 70)
                    print("TEST 3: Skipped (no tools available)")
                    print("=" * 70)

            print("\n" + "=" * 70)
            print("All tests completed!")
            print("=" * 70)

        except Exception as e:
            print(f"\nError during testing: {e}")

        finally:
            # Clean up
            print("\nShutting down MCP server...")
            process.terminate()
            process.wait(timeout=5)
            print("✓ MCP server stopped")

    except FileNotFoundError:
        print("\n✗ Error: Could not find phase4_mcp_server.py")
        print("Make sure you're running this from the repository root")

    except Exception as e:
        print(f"\n✗ Error: {e}")


if __name__ == "__main__":
    main()
