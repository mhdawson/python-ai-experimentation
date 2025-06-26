# Llama Stack guardrails example with Python

Initially converted from the JavaScript version in
[ai-tool-experimentation/llama-stack-rag](https://github.com/mhdawson/ai-tool-experimentation/tree/main/llama-stack-rag)
to Python with assistance from cursor with Claude-4-sonnet 

## Installing

1) clone the repository and move to python-ai-experimentation/llama-stack-rag
   directory

```bash
   git clone https://github.com/mhdawson/python-ai-experimentation.git
   cd python-ai-experimentation/llama-stack-rag
```

2) install requirements 

```bash
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
```

## Running

Update the MODEL_ID and base_url in llama-stack-agent-rag.py and
llama-stack-chat-rag.py to point to the Llama Stack instance you
want to use along with the name of the model 

```
model_id = "meta-llama/Llama-3.1-8B-instruct-q4_K_M"
SHOW_RAG_DOCUMENTS = False

# Initialize client
client = LlamaStackClient(
    base_url="http://10.1.2.128:8321",
    timeout=120.0,
)
```

Then run:

```bash
python llama-stack-agent-rag.py
```

or

```bash
python llama-stack-chat-rag.py
```
