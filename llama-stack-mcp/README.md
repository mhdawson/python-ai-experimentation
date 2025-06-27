# Llama Stack mcp examples with Python

Initially converted from the JavaScript version in
[ai-tool-experimentation/mcp](https://github.com/mhdawson/ai-tool-experimentation/tree/main/mcp)
to Python with assistance from cursor with Claude-4-sonnet 

## Installing

1) clone the repository and move to python-ai-experimentation/llama-stack-mcp
   directory

```bash
   git clone https://github.com/mhdawson/python-ai-experimentation.git
   cd python-ai-experimentation/llama-stack-mcp
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
model_id = "meta-llama/Llama-3.1-8B-Instruct"

client = LlamaStackClient(
    base_url="http://10.1.2.128:8321",
    timeout=120.0,
)
```

Then run:

```bash
python llama-stack-local-mcp.mjs
```

or

```bash
python llama-stack-agent-mcp.mjs
```

When running llama-stack-agent-mcp.mjs you will need to have already run the
script `start-mcp-server-for-llama-stack.sh` to start the mcp server on the
same host that your Llama Stack instance is running. This requires
Node.js and npm to be installed as supergateway is used to proxy the
requests to the mcp server written in Python. In addition you will
also need to have run `llama-stack-register-mcp.py` to register the
mcp server with Llama Stack.


