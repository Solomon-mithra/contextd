from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.db import (
    count_files,
    create_folder,
    create_index_job,
    finish_index_job,
    get_folder_by_path,
    init_db,
    latest_jobs,
    list_folders,
    mark_missing_files_deleted,
    upsert_file,
)
from core.discovery import discover_files


app = FastAPI(title="Relevect API", version="0.1.0")

# Keep DB initialization eager so the app works in both server mode and tests.
init_db()


@app.on_event("startup")
def startup() -> None:
    init_db()


class FolderCreateRequest(BaseModel):
    path: str = Field(..., description="Absolute path to a local folder")


class ScanRequest(BaseModel):
    folder_id: str | None = Field(
        None,
        description="Optional folder ID. If omitted, scans all active folders.",
    )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/folders")
def add_folder(req: FolderCreateRequest) -> dict[str, Any]:
    candidate = Path(req.path).expanduser().resolve()

    if not candidate.exists() or not candidate.is_dir():
        raise HTTPException(status_code=400, detail="Path does not exist or is not a directory")

    normalized = str(candidate)
    existing = get_folder_by_path(normalized)
    if existing:
        raise HTTPException(status_code=409, detail="Folder already registered")

    created = create_folder(normalized)
    return {
        "id": created.id,
        "path": created.path,
        "is_active": created.is_active,
        "created_at": created.created_at,
    }


@app.get("/folders")
def get_folders() -> dict[str, Any]:
    items = list_folders(active_only=False)
    return {
        "folders": [
            {
                "id": f.id,
                "path": f.path,
                "is_active": f.is_active,
                "created_at": f.created_at,
                "updated_at": f.updated_at,
            }
            for f in items
        ]
    }


@app.post("/index/scan")
def index_scan(req: ScanRequest) -> dict[str, Any]:
    folders = list_folders(active_only=True)
    if req.folder_id is not None:
        folders = [f for f in folders if f.id == req.folder_id]

    if not folders:
        raise HTTPException(status_code=404, detail="No active folders to scan")

    job_id = create_index_job(job_type="scan", status="running")

    try:
        total_discovered = 0
        total_deleted = 0

        for folder in folders:
            discovered = discover_files(folder.path)
            seen_paths: set[str] = set()

            for item in discovered:
                upsert_file(
                    folder_id=folder.id,
                    path=item.path,
                    file_name=item.file_name,
                    extension=item.extension,
                    size_bytes=item.size_bytes,
                    mtime=item.mtime,
                    status="discovered",
                )
                seen_paths.add(item.path)

            total_discovered += len(discovered)
            total_deleted += mark_missing_files_deleted(folder.id, seen_paths)

        finish_index_job(job_id, status="completed")

        return {
            "job_id": job_id,
            "scanned_folders": len(folders),
            "discovered_files": total_discovered,
            "marked_deleted_files": total_deleted,
        }
    except Exception as exc:  # pragma: no cover - safety catch for API response shape
        finish_index_job(job_id, status="failed", error=str(exc))
        raise HTTPException(status_code=500, detail="Scan failed")


@app.get("/index/status")
def index_status() -> dict[str, Any]:
    return {
        "files": count_files(),
        "recent_jobs": latest_jobs(limit=10),
    }
