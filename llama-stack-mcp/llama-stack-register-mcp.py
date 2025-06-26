#!/usr/bin/env python3
import logging
from llama_stack_client import LlamaStackClient

logging.getLogger("httpx").setLevel(logging.WARNING)


def main():
    client = LlamaStackClient(
        base_url="http://10.1.2.128:8321",
        timeout=120.0,
    )

    try:
        # Register the MCP toolgroup
        client.toolgroups.register(
            toolgroup_id="mcp::mcp_favorites",
            provider_id="model-context-protocol",
            mcp_endpoint={"uri": "http://10.1.2.128:8002/sse"},
        )
        print("Successfully registered MCP toolgroup: mcp::mcp_favorites")
    except Exception as e:
        print(f"Error registering MCP toolgroup: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
