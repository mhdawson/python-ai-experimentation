# Llama Stack Rag with python and Node.js Ref Arch

A simple app to use the
[Node.js Reference Architecture](https://github.com/nodeshift/nodejs-reference-architecture)
to answer questions using
[Retrieval Augmented Generation](https://www.redhat.com/en/topics/ai/what-is-retrieval-augmented-generation)

Initially generated with assistance from cursor with Claude-4-sonnet 


## Installing

1) clone the repository and move to python-ai-experimentation directory

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

3) clone the Node.js reference architecture repository

```bash
   git clone https://github.com/nodeshift/nodejs-reference-architecture.git
```

## Running

run

```bash
python llama-stack-rag1.py
```
