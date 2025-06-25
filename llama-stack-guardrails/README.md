# Llama Stack guardrails example with Python

Initially converted from the JavaScript version in
[ai-tool-experimentation/llama-stack-guardrails](https://github.com/mhdawson/ai-tool-experimentation/tree/main/llama-stack-guardrails)
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

Update the MODEL_ID and base_url in llama-stack-guardrails.py to point to the Llama Stack
instance you want to use along with the name of the model 

```
MODEL_ID = "meta-llama/Llama-3.1-8B-Instruct"
INCLUDE_SHIELDS = True

client = LlamaStackClient(
    base_url="http://10.1.2.128:8321",
    timeout=120.0,
)

```

Then run:

```bash
python llama-stack-guardrails.py
```
