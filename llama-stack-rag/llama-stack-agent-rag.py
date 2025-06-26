#!/usr/bin/env python3

import uuid
import logging
from pathlib import Path
from llama_stack_client import LlamaStackClient
from strip_markdown import strip_markdown

# remove logging we otherwise get by default
logging.getLogger("httpx").setLevel(logging.WARNING)

# Configuration
model_id = "meta-llama/Llama-3.1-8B-Instruct"
SHOW_RAG_DOCUMENTS = True

# Initialize client
client = LlamaStackClient(
    base_url="http://10.1.2.128:8321",
    timeout=120.0,
)


def main():
    ########################
    # Create the RAG database

    # use the first available provider
    providers = client.providers.list()
    provider = next(p for p in providers if p.api == "vector_io")

    # register a vector database
    vector_db_id = f"test-vector-db-{uuid.uuid4()}"
    client.vector_dbs.register(
        vector_db_id=vector_db_id,
        provider_id=provider.provider_id,
        embedding_model="all-MiniLM-L6-v2",
    )

    # read in all of the files to be used with RAG
    rag_documents = []
    docs_path = Path("/home/user1/newpull/nodejs-reference-architecture/docs")

    i = 0
    for file_path in docs_path.rglob("*.md"):
        i += 1
        if file_path.is_file():
            with open(file_path, "r", encoding="utf-8") as f:
                contents = f.read()

            # Convert markdown to plain text using strip_markdown
            plain_text = strip_markdown(contents)

            rag_documents.append(
                {
                    "document_id": f"doc-{i}",
                    "content": plain_text,
                    "mime_type": "text/plain",
                    "metadata": {},
                }
            )

    client.tool_runtime.rag_tool.insert(
        documents=rag_documents,
        vector_db_id=vector_db_id,
        chunk_size_in_tokens=126,
    )

    ########################
    # Create the agent

    agentic_system_create_response = client.agents.create(
        agent_config={
            "model": model_id,
            "instructions": "You are a helpful assistant, answer questions only based on information in the documents provided",
            "toolgroups": [
                {
                    "name": "builtin::rag/knowledge_search",
                    "args": {"vector_db_ids": [vector_db_id]},
                }
            ],
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

    questions = ["Should I use npm to start a node.js application"]

    for j in range(1):
        print(
            f"Iteration {j} ------------------------------------------------------------"
        )

        for i, question in enumerate(questions):
            print("QUESTION: " + question)

            response_stream = client.agents.turn.create(
                agent_id=agent_id,
                session_id=session_id,
                stream=True,
                messages=[{"role": "user", "content": question}],
            )

            # Handle streaming response
            response = ""
            for chunk in response_stream:
                if hasattr(chunk, "event") and hasattr(chunk.event, "payload"):
                    if chunk.event.payload.event_type == "turn_complete":
                        response = (
                            response + chunk.event.payload.turn.output_message.content
                        )
                    elif (
                        chunk.event.payload.event_type == "step_complete"
                        and chunk.event.payload.step_type == "tool_execution"
                        and SHOW_RAG_DOCUMENTS
                    ):
                        # Extract and print RAG document content in readable format
                        step_details = chunk.event.payload.step_details
                        if (
                            hasattr(step_details, "tool_responses")
                            and step_details.tool_responses
                        ):
                            print("\n" + "=" * 60)
                            print("RAG DOCUMENTS RETRIEVED")
                            print("=" * 60)

                            for tool_response in step_details.tool_responses:
                                if (
                                    hasattr(tool_response, "content")
                                    and tool_response.content
                                ):
                                    for item in tool_response.content:
                                        if (
                                            hasattr(item, "text")
                                            and "Result" in item.text
                                        ):
                                            # This is a result item, extract the content
                                            text = item.text
                                            if "Content:" in text:
                                                # Extract content after "Content:"
                                                content_start = text.find(
                                                    "Content:"
                                                ) + len("Content:")
                                                content_end = text.find("\nMetadata:")
                                                if content_end == -1:
                                                    content_end = len(text)

                                                content = text[
                                                    content_start:content_end
                                                ].strip()
                                                result_num = (
                                                    text.split("\n")[0]
                                                    if "\n" in text
                                                    else "Result"
                                                )

                                                print(f"\n--- {result_num} ---")
                                                print(content)
                                                print("-" * 40)
                            print("=" * 60)

            print("  RESPONSE:" + response)

    ########################
    # REMOVE DATABASE
    client.vector_dbs.unregister(vector_db_id)


if __name__ == "__main__":
    main()
