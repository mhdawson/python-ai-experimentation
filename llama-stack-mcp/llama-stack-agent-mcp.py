#!/usr/bin/env python3
import logging
from llama_stack_client import LlamaStackClient

logging.getLogger("httpx").setLevel(logging.WARNING)

model_id = "meta-llama/Llama-3.1-8B-Instruct"

client = LlamaStackClient(
    base_url="http://10.1.2.128:8321",
    timeout=120.0,
)


def main():
    # Create the agent
    agentic_system_create_response = client.agents.create(
        agent_config={
            "model": model_id,
            "instructions": "You are a helpful assistant",
            "toolgroups": ["mcp::mcp_favorites"],
            "tool_choice": "auto",
            "input_shields": [],
            "output_shields": [],
            "max_infer_iters": 10,
        }
    )
    agent_id = agentic_system_create_response.agent_id

    # Create a session that will be used to ask the agent a sequence of questions
    session_create_response = client.agents.session.create(
        agent_id, session_name="agent1"
    )
    session_id = session_create_response.session_id

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
        print(
            f"Iteration {j} ------------------------------------------------------------"
        )

        for i, question in enumerate(questions):
            print("QUESTION: " + question)
            response_stream = client.agents.turn.create(
                session_id,
                agent_id=agent_id,
                stream=True,
                messages=[{"role": "user", "content": question}],
            )

            # as of March 2025 only streaming was supported
            response = ""
            for chunk in response_stream:
                # Check for errors in the response
                if hasattr(chunk, "error") and getattr(chunk, "error", None):
                    error_msg = getattr(chunk, "error", {}).get(
                        "message", "Unknown error"
                    )
                    print(f"  ERROR: {error_msg}")
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
            print("  RESPONSE:" + response)


if __name__ == "__main__":
    main()
