# Relevect MCP Server

This folder contains a standalone MCP server that wraps the existing Relevect engine without modifying the current FastAPI app or desktop UI.

It is implemented with the official Python MCP SDK (`mcp` / `FastMCP`) and is intended for Claude Desktop connector usage.

## What It Exposes

The server runs over stdio and provides a single MCP tool:

- `search`

## Why It Is Separate

The MCP layer imports and reuses the current `core/*` search modules directly. That keeps:

- the FastAPI API unchanged
- the desktop app unchanged
- the indexed search logic shared

## Run

From the repo root:

```bash
.venv/bin/python mcp_server/server.py
```

This is a stdio MCP server, so it is meant to be launched by an MCP client rather than used interactively by hand.

## Example Client Config

Recommended for this repo, so the MCP server uses the same dependencies as the main app:

```json
{
  "mcpServers": {
    "relevect": {
      "command": "/Users/solomonmithra/Documents/Work/Relevect/.venv/bin/python",
      "args": ["/Users/solomonmithra/Documents/Work/Relevect/mcp_server/server.py"]
    }
  }
}
```

## Notes

- It pins `RELEVECT_DB_PATH` to `/Users/solomonmithra/Documents/Work/Relevect/data/relevect.db` inside the MCP process so Claude Desktop does not depend on launch cwd semantics.
- It only searches what has already been indexed by the existing Relevect engine.
- It does not expose folder management, scanning, or indexing over MCP.
