# Relevect - Local Context Engine for AI Agents

Week 4 baseline implemented:

- SQLite metadata schema (`folders`, `files`, `index_jobs`, `chunks`)
- FastAPI service startup DB initialization
- Folder registration and listing
- Recursive file discovery for `.pdf`, `.md`, `.txt`
- Scan endpoint with deleted-file marking
- Manual file indexing endpoint
- Parser pipeline for `.txt`, `.md`, and `.pdf`
- Chunk creation with snippets and heading/page metadata
- Local sentence-transformers embeddings for chunks and queries
- Hybrid retrieval endpoint over indexed chunks with normalized semantic and lexical scores
- Pending-file detection after scans
- Bulk indexing pipeline for discovered/changed files
- Index status endpoint with file counters + recent jobs
- Search-only MCP server for Claude Desktop using the official Python MCP SDK

## Run

```bash
uvicorn api.main:app --reload
```

Default DB path: `./data/relevect.db`

Override with:

```bash
export RELEVECT_DB_PATH=/absolute/path/relevect.db
```

## Current API

- `GET /health`
- `POST /folders`
- `GET /folders`
- `DELETE /folders/{folder_id}`
- `POST /index/scan`
- `POST /index/file`
- `POST /index/files`
- `POST /index/run`
- `POST /search`
- `GET /index/status`
- `GET /files`
- `DELETE /files/{file_id}`
- `POST /admin/reset`

## MCP Server

Relevect also includes a separate MCP server in [mcp_server/README.md](/Users/solomonmithra/Documents/Work/Relevect/mcp_server/README.md).

Current MCP surface:

- `search`

It is implemented with the official Python MCP SDK and is intended for Claude Desktop connectors. It reuses the existing indexed Relevect corpus and does not expose scan/index management over MCP.

Run it directly:

```bash
.venv/bin/python mcp_server/server.py
```

Recommended Claude Desktop config:

```json
{
  "preferences": {
    "coworkScheduledTasksEnabled": true,
    "sidebarMode": "chat",
    "coworkWebSearchEnabled": true,
    "ccdScheduledTasksEnabled": true
  },
  "mcpServers": {
    "relevect": {
      "command": "/Users/solomonmithra/Documents/Work/Relevect/.venv/bin/python",
      "args": [
        "/Users/solomonmithra/Documents/Work/Relevect/mcp_server/server.py"
      ],
      "cwd": "/Users/solomonmithra/Documents/Work/Relevect"
    }
  }
}
```

Notes:

- The MCP server pins `RELEVECT_DB_PATH` to the repo-local database path inside the MCP process so Claude Desktop startup is not dependent on shell cwd behavior.
- Claude Desktop should be fully quit with `Cmd+Q` after config changes.

## Learning notes

- Metadata is intentionally in SQLite first, so behavior is easy to inspect.
- `discover_files()` in `core/discovery.py` is simple and deterministic on purpose.
- `parse_document()` in `core/parser.py` converts file types into a common internal shape.
- `chunk_document()` in `core/chunking.py` turns parsed sections into stable chunk records.
- `core/embeddings.py` now uses a local `sentence-transformers` model (`all-MiniLM-L6-v2` by default).
- `core/retrieval.py` adds BM25-style lexical ranking, exact-phrase boosts, and score normalization so one signal does not dominate purely because of numeric scale.
- `POST /index/run` is the first real pipeline endpoint: it processes all discovered, changed, failed, or model-stale files without manual per-file calls.
- `index_jobs` gives a basic operational trail for scans before we add a queue/watcher.
- The MCP server was intentionally separated from the FastAPI app so Claude/Desktop integration does not distort the core engine architecture.

## Desktop

A Tauri desktop shell is scaffolded in [desktop/README.md](/Users/solomonmithra/Documents/Work/Relevect/desktop/README.md).
