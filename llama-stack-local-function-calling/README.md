# Simple Llama Stack function calling with Python

Initially converted from the JavaScript version in
[ai-tool-experimentation/llama-stack](https://github.com/mhdawson/ai-tool-experimentation/tree/main/llama-stack)
to Python with assistance from cursor with Claude-4-sonnet 

## Installing

1) clone the repository and move to python-ai-experimentation/llama-stack-local-function-calling
   directory

```bash
   git clone https://github.com/mhdawson/python-ai-experimentation.git
   cd python-ai-experimentation/llama-stack-local-function-calling
```

2) install requirements 

```bash
   uv venv
   source .venv/bin/activate
   uv pip install -r requirements.txt
```

## Running

Update the model_id and base_url in favorite-color.py to point to the Llama Stack
instance you want to use along with the name of the model 

```
model_id = "meta-llama/Llama-3.1-8B-Instruct"

client = LlamaStackClient(
    base_url="http://10.1.2.128:8321",
    timeout=120.0,
)
```

The run:

```bash
python favorite-color.py
```
