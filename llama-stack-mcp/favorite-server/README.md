# Favorite Server Python

Python implementation of the MCP favorite server, converted from the TypeScript original.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

Run the server:

```bash
python server.py
```

## Tools

The server provides two tools:

1. **favorite_color_tool**: Returns the favorite color for a person given their city and country
2. **favorite_hockey_tool**: Returns the favorite hockey team for a person given their city and country

### Supported Locations

- Ottawa, Canada
- Montreal, Canada

## MCP Protocol

This server implements the Model Context Protocol (MCP) using the FastMCP framework from the Python SDK. 
