# Relevect - Local Context Engine for AI Agents

Week 1 baseline implemented:

- SQLite metadata schema (`folders`, `files`, `index_jobs`, `chunks` placeholder)
- FastAPI service startup DB initialization
- Folder registration and listing
- Recursive file discovery for `.pdf`, `.md`, `.txt`
- Scan endpoint with deleted-file marking
- Index status endpoint with file counters + recent jobs

## Run

```bash
uvicorn api.main:app --reload
```

Default DB path: `./data/relevect.db`

Override with:

```bash
export RELEVECT_DB_PATH=/absolute/path/relevect.db
```

## Week 1 API

- `GET /health`
- `POST /folders`
- `GET /folders`
- `POST /index/scan`
- `GET /index/status`

## Learning notes

- Metadata is intentionally in SQLite first, so behavior is easy to inspect.
- `discover_files()` in `core/discovery.py` is simple and deterministic on purpose.
- `index_jobs` gives a basic operational trail for scans before we add a queue/watcher.
