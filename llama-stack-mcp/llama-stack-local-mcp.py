#!/usr/bin/env python3

import logging
import asyncio
import os
from typing import List, Dict
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


async def handle_response(
    messages: List[Dict], response, mcp_session, available_tools
) -> str:
    """Handle responses which may include a request to run a function"""

    # Push the model's response to the chat (in API-compatible format)
    # Convert completion_message to proper dict format first
    completion_message_dict = {
        "role": response.completion_message.role,
        "content": response.completion_message.content,
        "stop_reason": getattr(response.completion_message, "stop_reason", None),
        "tool_calls": getattr(response.completion_message, "tool_calls", None),
    }
    messages.append(completion_message_dict)

    # Check if there are tool calls to handle
    if (
        hasattr(response.completion_message, "tool_calls")
        and response.completion_message.tool_calls
        and len(response.completion_message.tool_calls) > 0
    ):

        for tool_call in response.completion_message.tool_calls:
            # Log the function calls so that we see when they are called
            log(f"  FUNCTION CALLED WITH: {tool_call}")
            print(f"  CALLED: {tool_call.tool_name}")

            try:
                # Call the MCP server tool
                func_response = await mcp_session.call_tool(
                    tool_call.tool_name, arguments=tool_call.arguments or {}
                )

                # Add tool responses to messages (in API-compatible format)
                if func_response.content:
                    for content_item in func_response.content:
                        if (
                            hasattr(content_item, "type")
                            and content_item.type == "text"
                        ):
                            messages.append(
                                {
                                    "role": "tool",
                                    "content": str(content_item.text),
                                    "call_id": str(tool_call.call_id),
                                    "tool_name": str(tool_call.tool_name),
                                }
                            )
                        else:
                            messages.append(
                                {
                                    "role": "tool",
                                    "content": str(content_item),
                                    "call_id": str(tool_call.call_id),
                                    "tool_name": str(tool_call.tool_name),
                                }
                            )
            except Exception as e:
                messages.append(
                    {
                        "role": "tool",
                        "content": f"tool call failed: {e}",
                        "call_id": getattr(tool_call, "call_id", "unknown"),
                        "tool_name": tool_call.tool_name,
                    }
                )

        # Call the model again so that it can process the data returned by the function calls
        # (same as JavaScript version - use the same messages array with tool results added)
        try:
            # Call the model again with the conversation history including tool results
            next_response = client.inference.chat_completion(
                messages=messages,
                model_id=model_id,
                tools=available_tools,
            )

            # Recursively call handleResponse with the same messages array (like JavaScript)
            return await handle_response(
                messages, next_response, mcp_session, available_tools
            )

        except Exception as e:
            return f"Error processing tool results: {e}"

    else:
        # No function calls, just return the response
        return str(response.completion_message.content)


async def main():
    """Main function that handles MCP server communication and tool calls"""

    # Server parameters for the Python favorite server
    server_params = StdioServerParameters(
        command="python",
        args=[os.path.abspath("favorite-server/server.py")],
        env=None,
    )

    # Connect to the MCP server
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as mcp_session:
            # Initialize the connection
            await mcp_session.initialize()

            #####################################
            # Start MCP server and get the available tools from the MCP server
            tools_response = await mcp_session.list_tools()
            tools_list = tools_response.tools

            #############################
            # Convert the description of the tools to the format needed by llama-stack
            # (exactly like JavaScript version)
            available_tools = []
            for tool in tools_list:
                # Convert tool object in place like JavaScript version
                tool_dict = {
                    "tool_name": tool.name,
                    "description": tool.description,
                    "parameters": (
                        tool.inputSchema.get("properties", {})
                        if hasattr(tool, "inputSchema")
                        else {}
                    ),
                }

                # Convert parameter format exactly like JavaScript
                if (
                    hasattr(tool, "inputSchema")
                    and tool.inputSchema
                    and "properties" in tool.inputSchema
                ):
                    for param_name, parameter in tool_dict["parameters"].items():
                        # Convert type to param_type like JavaScript
                        if "type" in parameter:
                            parameter["param_type"] = parameter["type"]
                            del parameter["type"]

                        # Add required flag like JavaScript
                        if (
                            "required" in tool.inputSchema
                            and param_name in tool.inputSchema["required"]
                        ):
                            parameter["required"] = True

                available_tools.append(tool_dict)

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
                "What is my favorite hockey team ?",
                "My city is Montreal and my country is Canada",
                "Who was the first president of the United States?",
            ]

            for j in range(1):
                # Maintains chat history (same as JavaScript version)
                messages = [
                    {
                        "role": "system",
                        "content": (
                            "only answer questions about a favorite color by using the response from the favorite_color_tool "
                            "only answer questions about a favorite hockey team by using the response from the favorite_hockey_tool "
                            "when asked for a favorite color if you have not called the favorite_color_tool, call it "
                            "if the assistance does not have the parameters to call a tool, ask the user for them by name"
                            "Never guess a favorite color "
                            "Do not be chatty "
                            "Give short answers when possible"
                        ),
                    }
                ]

                print(f"\nIteration {j} " + "-" * 60)

                for i, question in enumerate(questions):
                    print(f"QUESTION: {question}")
                    messages.append({"role": "user", "content": question})

                    try:
                        # Call the inference API with tools (same as JavaScript version)
                        # For now, use simple message format to avoid type issues
                        simple_messages = []
                        for msg in messages:
                            if msg["role"] in ["user", "system"]:
                                simple_messages.append(
                                    {"role": msg["role"], "content": msg["content"]}
                                )

                        response = client.inference.chat_completion(
                            messages=simple_messages,
                            model_id=model_id,
                            tools=available_tools,
                        )

                        # Use handleResponse to process the response and any tool calls
                        answer = await handle_response(
                            messages, response, mcp_session, available_tools
                        )
                        print(f"  RESPONSE: {answer}")

                    except Exception as e:
                        print(f"  ERROR: {e}")
                        # Continue with next question
                        continue


def run_main():
    """Synchronous wrapper for the async main function"""
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit(run_main())
