#!/usr/bin/env python3

import uuid
import logging
from pathlib import Path
from llama_stack_client import LlamaStackClient
from strip_markdown import strip_markdown

# remove logging we otherwise get by default
logging.getLogger("httpx").setLevel(logging.WARNING)

# Configuration
model_id = "meta-llama/Llama-3.1-8B-instruct-q4_K_M"
SHOW_RAG_DOCUMENTS = False

# Initialize client
client = LlamaStackClient(
    base_url="http://10.1.2.128:8321",
    timeout=120.0,
)


def main():
    ########################
    # Register the model we would like to use from ollama
    client.models.register(
        model_id=model_id,
        provider_id="ollama",
        provider_model_id="llama3.1:8b-instruct-q4_K_M",
        model_type="llm",
    )

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
        chunk_size_in_tokens=125,
    )

    #############################
    # ASK QUESTIONS

    questions = ["Should I use npm to start an application"]

    for j in range(1):
        # maintains chat history
        messages = [
            {
                "role": "system",
                "content": "Give short answers when possible",
            }
        ]

        print(
            f"Iteration {j} ------------------------------------------------------------"
        )

        for i, question in enumerate(questions):
            print("QUESTION: " + question)

            raw_rag_results = client.tool_runtime.rag_tool.query(
                content=question,
                vector_db_ids=[vector_db_id],
            )

            rag_results = []
            for content_item in raw_rag_results.content:
                rag_results.append(str(content_item.text))

            if SHOW_RAG_DOCUMENTS:
                for result in rag_results:
                    print(result)

            prompt = f"""Answer the question based only on the context provided
                   <question>{question}</question>
                   <context>{' '.join(rag_results)}</context>"""

            messages.append({"role": "user", "content": prompt})
            response = client.inference.chat_completion(
                messages=messages,
                model_id=model_id,
            )

            print("  RESPONSE:" + response.completion_message.content)

    ########################
    # REMOVE DATABASE
    client.vector_dbs.unregister(vector_db_id)


if __name__ == "__main__":
    main()
