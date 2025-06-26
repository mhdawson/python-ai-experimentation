#!/usr/bin/env python3

import os
import sys
from pathlib import Path

from llama_stack_client import LlamaStackClient
from llama_stack_client.types.shared_params import Document

# Configuration
LLAMA_STACK_URL = "http://10.1.2.128:8321"
MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
TIMEOUT = 120
QUESTION = "Should I use npm to start a node.js application?"
KNOWLEDGE_BANK_ID = "nodejs-reference-architecture"
MARKDOWN_DIR = "nodejs-reference-architecture"


def _create_vector_database(client: LlamaStackClient, knowledge_bank_id: str) -> None:
    """Create a vector database for the knowledge bank."""
    try:
        vector_db_response = client._client.post(
            "/v1/vector-dbs",
            json={
                "vector_db_id": knowledge_bank_id,
                "provider_id": "faiss",
                "embedding_model": "all-MiniLM-L6-v2",
                "embedding_dimension": 384,
            },
        )
        if vector_db_response.status_code == 200:
            print(f"✅ Created vector database: {knowledge_bank_id}")
        else:
            print(f"⚠️  Vector database creation response: {vector_db_response.status_code}")
            print(f"    Response: {vector_db_response.text}")
    except Exception as e:
        if "already exists" in str(e).lower() or "conflict" in str(e).lower():
            print(f"✅ Vector database {knowledge_bank_id} already exists")
        else:
            print(f"⚠️  Vector database creation issue: {e}")
            print("💾 Proceeding with existing configuration")


def _find_markdown_files(directory: str) -> list:
    """Find all markdown files in the directory."""
    md_files = []
    for root, _dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                md_files.append(Path(root) / file)
    return md_files


def _process_markdown_file(
    client: LlamaStackClient, md_file: str, directory: str, knowledge_bank_id: str
) -> tuple[bool, int]:
    """Process a single markdown file using Llama Stack's built-in document splitting."""
    try:
        with Path(md_file).open(encoding="utf-8") as f:
            content = f.read()

        if not content.strip():  # Skip empty files
            return False, 0

        # Convert Path to string to ensure JSON serialization
        md_file_str = str(md_file)

        # Create document ID from file path
        doc_id = (
            Path(md_file).name.replace(directory + "/", "").replace("/", "_").replace(".md", "")
        )
        doc_title = Path(md_file).name.replace(".md", "")

        print(f"📝 Processing: {md_file_str}")

        # Create a Document object using the Llama Stack client types
        # This lets Llama Stack handle the chunking internally
        document = Document(
            document_id=doc_id,
            content=content,
            mime_type="text/markdown",
            metadata={
                "source": md_file_str,
                "type": "markdown",
                "title": doc_title,
            },
        )

        print("   📄 Sending full document to Llama Stack for automatic chunking")

        # Use the RAG tool to insert the document with automatic chunking
        try:
            client.tool_runtime.rag_tool.insert(
                documents=[document],
                vector_db_id=knowledge_bank_id,
                chunk_size_in_tokens=128,  # Let Llama Stack handle optimal chunking
            )
            print(
                "   ✅ Document processed successfully (Llama Stack created chunks automatically)"
            )
            return True, 1  # Return 1 as we processed 1 document (chunks handled internally)
        except Exception as e:
            print(f"   ⚠️  Error with RAG tool, trying vector_io.insert: {e}")
            # Fallback to vector_io.insert if RAG tool is not available
            client.vector_io.insert(
                vector_db_id=knowledge_bank_id,
                chunks=[
                    {
                        "content": content,
                        "metadata": {
                            "document_id": doc_id,
                            "source": md_file_str,
                            "type": "markdown",
                            "title": doc_title,
                        },
                    }
                ],
            )
            print("   ✅ Document processed with vector_io.insert (manual chunking)")
            return True, 1

    except Exception as e:
        print(f"❌ Error processing {md_file}: {e}")
        return False, 0


def _ingest_markdown_documents(client: LlamaStackClient, directory: str, knowledge_bank_id: str):
    """
    Ingest markdown documents from a directory into Llama Stack's knowledge bank.
    Uses Llama Stack's built-in document splitting functionality.

    Args:
        client: The Llama Stack client instance
        directory: Directory containing markdown files
        knowledge_bank_id: ID for the knowledge bank to store documents
    """
    print(f"📚 Ingesting markdown documents from {directory}...")
    print("🔧 Using Llama Stack's built-in document splitting functionality")

    try:
        # Create vector database using the faiss provider
        _create_vector_database(client, knowledge_bank_id)

        # Find all markdown files
        md_files = _find_markdown_files(directory)
        print(f"📄 Found {len(md_files)} markdown files")

        # Process each markdown file
        documents_added = 0
        chunks_added = 0
        for md_file in md_files:
            success, chunk_count = _process_markdown_file(
                client, md_file, directory, knowledge_bank_id
            )
            if success:
                documents_added += 1
                chunks_added += chunk_count

        print(
            f"✅ Successfully ingested {documents_added} documents (Llama Stack created chunks automatically) into knowledge bank"
        )
        return True

    except Exception as e:
        print(f"❌ Error during document ingestion: {e}")
        return False


def _check_vector_database_exists_and_has_content(
    client: LlamaStackClient, knowledge_bank_id: str
) -> bool:
    """
    Check if the vector database exists and contains documents.

    Args:
        client: The Llama Stack client instance
        knowledge_bank_id: ID of the knowledge bank to check

    Returns:
        True if the database exists and has content, False otherwise
    """
    try:
        # Try to query the vector database with a simple test query
        results = client.vector_io.query(
            vector_db_id=knowledge_bank_id, query="test", params={"limit": 1}
        )

        # If we get results, the database exists and has content
        if hasattr(results, "chunks") and results.chunks:
            print(f"✅ Vector database '{knowledge_bank_id}' exists and contains documents")
            return True
        print(f"📭 Vector database '{knowledge_bank_id}' exists but is empty")
        return False

    except Exception as e:
        error_str = str(e).lower()
        if "not served" in error_str or "not found" in error_str or "invalid value" in error_str:
            print(f"❌ Vector database '{knowledge_bank_id}' does not exist")
            return False
        print(f"⚠️  Error checking vector database: {e}")
        return False


def _retrieve_relevant_documents(
    client: LlamaStackClient, query: str, knowledge_bank_id: str, top_k: int = 5
):
    """
    Retrieve relevant documents from the knowledge bank based on the query.

    Args:
        client: The Llama Stack client instance
        query: The search query
        knowledge_bank_id: ID of the knowledge bank to search
        top_k: Number of top relevant documents to retrieve

    Returns:
        Tuple of (document_contents, document_info) where:
        - document_contents: List of relevant document contents
        - document_info: List of document metadata for display
    """
    try:
        print(f"🔍 Searching for relevant documents for query: '{query}'")

        # Query the vector database
        results = client.vector_io.query(
            vector_db_id=knowledge_bank_id, query=query, params={"limit": top_k}
        )

        if hasattr(results, "chunks") and results.chunks:
            print(f"📚 Found {len(results.chunks)} relevant document chunks")

            # Extract content and metadata
            document_contents = []
            document_info = []

            for i, chunk in enumerate(results.chunks, 1):
                document_contents.append(chunk.content)

                # Extract metadata for display
                metadata = getattr(chunk, "metadata", {})
                doc_title = metadata.get("title", f"Document {i}")
                doc_source = metadata.get("source", "Unknown source")
                doc_type = metadata.get("type", "unknown")
                chunk_index = metadata.get("chunk_index", "Auto-generated")
                total_chunks = metadata.get("total_chunks", "Auto-managed")

                # Get a preview of the content (first 100 chars)
                content_str = (
                    str(chunk.content) if not isinstance(chunk.content, str) else chunk.content
                )
                content_preview = (
                    content_str[:100] + "..." if len(content_str) > 100 else content_str
                )

                document_info.append(
                    {
                        "index": i,
                        "title": doc_title,
                        "source": doc_source,
                        "type": doc_type,
                        "preview": content_preview,
                        "chunk_index": chunk_index,
                        "total_chunks": total_chunks,
                    }
                )

            # Display retrieved documents with full content
            print("\n📄 Retrieved Document Chunks (Full Content):")
            print("=" * 80)
            for i, (doc_info, content) in enumerate(zip(document_info, document_contents), 1):
                chunk_info = (
                    f" (Chunk {doc_info['chunk_index']}/{doc_info['total_chunks']})"
                    if doc_info["chunk_index"] != "Auto-generated"
                    else " (Auto-chunked by Llama Stack)"
                )
                print(f"\n📌 Chunk {i}: {doc_info['title']}{chunk_info}")
                print(f"📂 Source: {doc_info['source']}")
                print(f"🏷️  Type: {doc_info['type']}")
                print("-" * 60)
                print(content)
                print("-" * 60)

            return document_contents, document_info
        print("📚 No relevant documents found")
        return [], []

    except Exception as e:
        print(f"❌ Error retrieving documents: {e}")
        return [], []


def _query_llama_stack_with_rag(
    url: str,
    model: str,
    message: str,
    knowledge_bank_id: str,
    timeout: int = 120,
    use_rag: bool = True,
):
    """
    Query the Llama Stack instance with RAG-enhanced context using the official SDK.

    Args:
        url: The base URL of the Llama Stack instance
        model: The model name to use
        message: The message/question to send
        knowledge_bank_id: ID of the knowledge bank for RAG
        timeout: Request timeout in seconds
        use_rag: Whether to use RAG for context enhancement

    Returns:
        Response object from the Llama Stack client

    Raises:
        Exception: If the request fails
    """

    print(f"🚀 Querying Llama Stack at: {url}")
    print(f"📝 Model: {model}")
    print(f"❓ Question: {message}")
    print(f"⏱️  Timeout: {timeout} seconds")
    print(f"🧠 RAG Enabled: {use_rag}")
    print("-" * 50)

    # Initialize the Llama Stack client
    client = LlamaStackClient(
        base_url=url,
        timeout=timeout,
    )

    # Enhanced message with context
    enhanced_message = message

    if use_rag:
        try:
            # Retrieve relevant documents
            relevant_docs, doc_info = _retrieve_relevant_documents(
                client, message, knowledge_bank_id
            )

            if relevant_docs:
                # Create context from relevant documents
                context = "\n\n".join(
                    [f"Document {i+1}:\n{doc}" for i, doc in enumerate(relevant_docs)]
                )

                # Enhance the prompt with context
                enhanced_message = f"""Based on the following context from the Node.js Reference Architecture documentation, please answer the question.

Context:
{context}

Question: {message}

Please provide a comprehensive answer using the context provided above."""

                print(f"📚 Enhanced prompt with {len(relevant_docs)} relevant document(s)")
                print(f"📋 Context includes: {', '.join([info['title'] for info in doc_info])}")
                print(
                    f"🔗 Sources: {', '.join({info['source'].split('/')[-1] for info in doc_info})}"
                )
            else:
                print("📚 No relevant documents found, using original question")

        except Exception as e:
            print(f"⚠️  RAG retrieval failed: {e}")
            print("📚 Proceeding with original question without RAG")

    try:
        # Make the inference request using the SDK with proper parameters
        return client.inference.chat_completion(
            model_id=model,
            messages=[{"role": "user", "content": enhanced_message}],
            sampling_params={
                "strategy": {"type": "greedy"},
                "max_tokens": 500,
            },
        )

    except Exception as e:
        raise Exception(f"Request failed: {e}") from e


def _format_response(response) -> str:
    """
    Format the response data for display using the Llama Stack client response.

    Args:
        response: The response object from the Llama Stack client

    Returns:
        Formatted string representation of the response
    """
    try:
        # Extract the main content from the Llama Stack SDK response
        if hasattr(response, "completion_message") and response.completion_message:
            content = response.completion_message.content

            return f"""✅ Response received successfully!

💬 LLM Response:
{content}
"""
        return f"❌ Unexpected response format: {response}"

    except Exception as e:
        return f"❌ Error formatting response: {e}\nRaw response: {response}"


def main():
    """Main function to run the Llama Stack query with RAG capabilities."""
    print("🦙 Llama Stack RAG-Enhanced Query Application")
    print("=" * 50)

    # Initialize the Llama Stack client
    client = LlamaStackClient(
        base_url=LLAMA_STACK_URL,
        timeout=TIMEOUT,
    )

    try:
        # Check if markdown directory exists
        if Path(MARKDOWN_DIR).exists():
            print(f"📁 Found markdown directory: {MARKDOWN_DIR}")

            # Check if vector database already exists and has content
            print("\n🔍 Checking if documents are already ingested...")
            has_content = _check_vector_database_exists_and_has_content(client, KNOWLEDGE_BANK_ID)

            if has_content:
                print("✅ Vector database already contains documents, skipping ingestion")
                use_rag = True
            else:
                # Ingest documents into knowledge bank
                print("\n📚 Starting document ingestion...")
                ingestion_success = _ingest_markdown_documents(
                    client, MARKDOWN_DIR, KNOWLEDGE_BANK_ID
                )

                if ingestion_success:
                    print("✅ Document ingestion completed successfully!")
                    use_rag = True
                else:
                    print("⚠️  Document ingestion failed, proceeding without RAG")
                    use_rag = False
        else:
            print(f"❌ Markdown directory not found: {MARKDOWN_DIR}")
            print("📚 Proceeding without RAG functionality")
            use_rag = False

        print("\n" + "=" * 50)

        # Query the Llama Stack with RAG enhancement
        response_data = _query_llama_stack_with_rag(
            url=LLAMA_STACK_URL,
            model=MODEL_NAME,
            message=QUESTION,
            knowledge_bank_id=KNOWLEDGE_BANK_ID,
            timeout=TIMEOUT,
            use_rag=use_rag,
        )

        # Format and display the response
        formatted_response = _format_response(response_data)
        print(formatted_response)

    except Exception as e:
        print(f"❌ Application failed: {e}")
        print("\n🔧 Troubleshooting tips:")
        print("1. Check if the Llama Stack instance is running")
        print("2. Verify the URL is correct and accessible")
        print("3. Ensure the model is available on the instance")
        print("4. Check your network connection")
        print("5. Verify the markdown directory exists")
        sys.exit(1)


if __name__ == "__main__":
    main()
