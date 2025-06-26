#!/usr/bin/env python3
"""
Llama Stack Local MCP with Python Server

This script demonstrates how to use a local Python MCP server with Llama Stack.
It directly spawns and connects to the Python MCP server from favorite-server-python/
instead of relying on external toolgroup registration.

Features:
1. Tests the MCP server directly to ensure it works
2. Registers the MCP server with Llama Stack
3. Creates an agent that can use the MCP tools
4. Runs a series of test questions to demonstrate functionality

The Python MCP server provides two tools:
- favorite_color_tool: Returns favorite colors for supported locations
- favorite_hockey_tool: Returns favorite hockey teams for supported locations

Supported locations: Ottawa, Canada and Montreal, Canada
"""

import logging
import asyncio
from llama_stack_client import LlamaStackClient
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Set up logging
logging.getLogger("httpx").setLevel(logging.WARNING)

model_id = "meta-llama/Llama-3.1-8B-Instruct"

client = LlamaStackClient(
    base_url="http://10.1.2.128:8321",
    timeout=120.0,
)

verbose = False


def log(message):
    if verbose:
        print(message)


async def test_mcp_server_directly():
    """Test the MCP server directly to verify it works"""
    print("Testing MCP server directly...")

    # Server parameters for the Python favorite server
    server_params = StdioServerParameters(
        command="python", args=["favorite-server/server.py"], env=None
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # List available tools
                tools = await session.list_tools()
                print("✅ MCP Server connected successfully!")
                print(f"Available tools: {[tool.name for tool in tools.tools]}")

                # Test the favorite_color_tool
                result = await session.call_tool(
                    "favorite_color_tool",
                    arguments={"city": "Ottawa", "country": "Canada"},
                )
                # Handle different content types safely
                if result.content and len(result.content) > 0:
                    content = result.content[0]
                    # Check if it's a TextContent type
                    if (
                        hasattr(content, "type")
                        and content.type == "text"
                        and hasattr(content, "text")
                    ):
                        print(f"Test result: {content.text}")
                    else:
                        print(f"Test result: {str(content)}")

                return True

    except Exception as e:
        print(f"❌ Error connecting to MCP server: {e}")
        return False


def register_mcp_server_with_llama_stack():
    """Register the MCP server with Llama Stack using subprocess approach"""
    print("Registering MCP server with Llama Stack...")

    try:
        # Register the MCP toolgroup pointing to our local Python server
        # Note: The exact format may vary depending on Llama Stack version
        client.toolgroups.register(
            toolgroup_id="mcp::local_favorites",
            provider_id="model-context-protocol",
            # For local development, try HTTP endpoint format
            mcp_endpoint={"uri": "http://localhost:8002/sse"},
        )
        print("✅ MCP toolgroup registered successfully!")
        return True

    except Exception as e:
        print(f"❌ Error registering MCP toolgroup: {e}")
        print("Note: This may fail if Llama Stack doesn't support stdio MCP endpoints")
        return False


def main():
    print("=== Llama Stack Local MCP with Python Server ===")
    print("Using the Python MCP server from favorite-server-python/")
    print()

    # First test the MCP server directly to make sure it works
    print("Step 1: Testing MCP server directly...")
    if not asyncio.run(test_mcp_server_directly()):
        print(
            "❌ MCP server test failed. Please check favorite-server-python/server.py"
        )
        return 1

    print("\nStep 2: Registering MCP server with Llama Stack...")

    # Try to register with Llama Stack
    # Note: This may not work if Llama Stack doesn't support local stdio MCP servers
    # In that case, we fall back to the toolgroup approach
    try:
        # Try the direct registration approach first
        if not register_mcp_server_with_llama_stack():
            print("Direct registration failed, falling back to toolgroup approach...")
            print("You may need to run 'python llama-stack-register-mcp.py' separately")
            print("and ensure the MCP server is running externally")

            # Use the external toolgroup approach
            toolgroup_id = "mcp::mcp_favorites"
        else:
            toolgroup_id = "mcp::local_favorites"

    except Exception as e:
        print(f"Registration error: {e}")
        print("Falling back to external toolgroup approach...")
        toolgroup_id = "mcp::mcp_favorites"

    # Create the agent with MCP toolgroup
    try:
        agentic_system_create_response = client.agents.create(
            agent_config={
                "model": model_id,
                "instructions": (
                    "only answer questions about a favorite color by using the response from the favorite_color_tool. "
                    "only answer questions about a favorite hockey team by using the response from the favorite_hockey_tool. "
                    "when asked for a favorite color if you have not called the favorite_color_tool, call it. "
                    "Never guess a favorite color. "
                    "Do not be chatty. "
                    "Give short answers when possible"
                ),
                "toolgroups": [toolgroup_id],
                "tool_choice": "auto",
                "input_shields": [],
                "output_shields": [],
                "max_infer_iters": 10,
            }
        )
        agent_id = agentic_system_create_response.agent_id
        print(f"✅ Agent created with ID: {agent_id}")

        # Create a session
        session_create_response = client.agents.session.create(
            agent_id, session_name="local_mcp_session"
        )
        session_id = session_create_response.session_id
        print(f"✅ Session created with ID: {session_id}")

    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        print("Make sure:")
        print("1. Llama Stack server is running")
        print("2. MCP toolgroup is properly registered")
        print("3. favorite-server-python/server.py is working")
        return 1

    print("\nStep 3: Testing agent with questions...")
    print("=" * 60)

    #############################
    # ASK QUESTIONS

    questions = [
        "What is my favorite color?",
        "My city is Ottawa",
        "My country is Canada",
        "I moved to Montreal. What is my favorite color now?",
        "My city is Montreal and my country is Canada",
        "What is the fastest car in the world?",
        "My city is Ottawa and my country is Canada, what is my favorite color?",
        "What is my favorite hockey team?",
        "My city is Montreal and my country is Canada",
        "Who was the first president of the United States?",
    ]

    for j in range(1):
        print(f"\nIteration {j+1}")
        print("-" * 60)

        for i, question in enumerate(questions):
            print(f"\nQUESTION {i+1}: {question}")
            try:
                response_stream = client.agents.turn.create(
                    session_id,
                    agent_id=agent_id,
                    stream=True,
                    messages=[{"role": "user", "content": question}],
                )

                response = ""
                for chunk in response_stream:
                    # Check for errors in the response
                    if hasattr(chunk, "error") and getattr(chunk, "error", None):
                        error_msg = getattr(chunk, "error", {}).get(
                            "message", "Unknown error"
                        )
                        print(f"  ❌ ERROR: {error_msg}")
                        break
                    # Check for successful turn completion
                    elif (
                        hasattr(chunk, "event")
                        and getattr(chunk, "event", None)
                        and hasattr(chunk.event, "payload")
                        and chunk.event.payload.event_type == "turn_complete"
                    ):
                        response = response + str(
                            chunk.event.payload.turn.output_message.content
                        )

                print(f"  RESPONSE: {response}")

            except Exception as e:
                print(f"  ❌ ERROR: {e}")

    print("\n" + "=" * 60)
    print("✅ Testing completed!")
    return 0


if __name__ == "__main__":
    exit(main())
