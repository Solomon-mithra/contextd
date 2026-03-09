import os
import sqlite3
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


DEFAULT_DB_PATH = "./data/relevect.db"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_db_path() -> str:
    return os.getenv("RELEVECT_DB_PATH", DEFAULT_DB_PATH)


def _ensure_parent_dir(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_conn() -> Iterable[sqlite3.Connection]:
    db_path = get_db_path()
    _ensure_parent_dir(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    schema_path = Path(__file__).with_name("schema.sql")
    with get_conn() as conn:
        conn.executescript(schema_path.read_text(encoding="utf-8"))


@dataclass(frozen=True)
class Folder:
    id: str
    path: str
    is_active: bool
    created_at: str
    updated_at: str


def _row_to_folder(row: sqlite3.Row) -> Folder:
    return Folder(
        id=row["id"],
        path=row["path"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def create_folder(path: str) -> Folder:
    ts = now_iso()
    folder_id = str(uuid.uuid4())

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO folders (id, path, is_active, created_at, updated_at)
            VALUES (?, ?, 1, ?, ?)
            """,
            (folder_id, path, ts, ts),
        )
        row = conn.execute("SELECT * FROM folders WHERE id = ?", (folder_id,)).fetchone()

    return _row_to_folder(row)


def get_folder_by_path(path: str) -> Optional[Folder]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM folders WHERE path = ?", (path,)).fetchone()
    return _row_to_folder(row) if row else None


def list_folders(active_only: bool = False) -> list[Folder]:
    sql = "SELECT * FROM folders"
    params: tuple[object, ...] = ()
    if active_only:
        sql += " WHERE is_active = 1"
    sql += " ORDER BY created_at ASC"

    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()

    return [_row_to_folder(r) for r in rows]


def upsert_file(
    *,
    folder_id: str,
    path: str,
    file_name: str,
    extension: str,
    size_bytes: int,
    mtime: float,
    status: str = "discovered",
) -> None:
    ts = now_iso()
    file_id = str(uuid.uuid4())

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO files (
                id, folder_id, path, file_name, extension, size_bytes, mtime,
                status, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(path) DO UPDATE SET
                folder_id=excluded.folder_id,
                file_name=excluded.file_name,
                extension=excluded.extension,
                size_bytes=excluded.size_bytes,
                mtime=excluded.mtime,
                status=excluded.status,
                updated_at=excluded.updated_at
            """,
            (
                file_id,
                folder_id,
                path,
                file_name,
                extension,
                size_bytes,
                mtime,
                status,
                ts,
                ts,
            ),
        )


def mark_missing_files_deleted(folder_id: str, seen_paths: set[str]) -> int:
    ts = now_iso()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT path FROM files WHERE folder_id = ? AND status != 'deleted'",
            (folder_id,),
        ).fetchall()
        existing_paths = {r["path"] for r in rows}
        deleted = existing_paths - seen_paths
        for p in deleted:
            conn.execute(
                "UPDATE files SET status='deleted', updated_at=? WHERE folder_id=? AND path=?",
                (ts, folder_id, p),
            )
    return len(deleted)


def count_files() -> dict[str, int]:
    with get_conn() as conn:
        total = conn.execute("SELECT COUNT(*) AS c FROM files").fetchone()["c"]
        discovered = conn.execute(
            "SELECT COUNT(*) AS c FROM files WHERE status = 'discovered'"
        ).fetchone()["c"]
        deleted = conn.execute(
            "SELECT COUNT(*) AS c FROM files WHERE status = 'deleted'"
        ).fetchone()["c"]
    return {"total": int(total), "discovered": int(discovered), "deleted": int(deleted)}


def create_index_job(job_type: str, status: str, file_id: Optional[str] = None) -> str:
    job_id = str(uuid.uuid4())
    ts = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO index_jobs (id, file_id, job_type, status, started_at, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (job_id, file_id, job_type, status, ts, ts),
        )
    return job_id


def finish_index_job(job_id: str, status: str, error: Optional[str] = None) -> None:
    ts = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE index_jobs
            SET status = ?, finished_at = ?, error = ?
            WHERE id = ?
            """,
            (status, ts, error, job_id),
        )


def latest_jobs(limit: int = 10) -> list[dict[str, object]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT id, file_id, job_type, status, started_at, finished_at, error
            FROM index_jobs
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()

    return [dict(r) for r in rows]
