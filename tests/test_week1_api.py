from pathlib import Path

from fastapi.testclient import TestClient


def test_week1_flow(tmp_path, monkeypatch):
    db_path = tmp_path / "relevect.db"
    monkeypatch.setenv("RELEVECT_DB_PATH", str(db_path))

    data_dir = tmp_path / "docs"
    data_dir.mkdir()
    (data_dir / "notes.md").write_text("# Notes\nhello", encoding="utf-8")
    (data_dir / "readme.txt").write_text("plain text", encoding="utf-8")
    (data_dir / "ignore.bin").write_bytes(b"\x00\x01")

    from api.main import app

    client = TestClient(app)

    # Health endpoint exists.
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json()["status"] == "ok"

    # Register folder.
    create = client.post("/folders", json={"path": str(data_dir)})
    assert create.status_code == 200
    folder_id = create.json()["id"]

    # Duplicate folder is rejected.
    dup = client.post("/folders", json={"path": str(data_dir)})
    assert dup.status_code == 409

    # Scan discovers supported files only.
    scan = client.post("/index/scan", json={"folder_id": folder_id})
    assert scan.status_code == 200
    assert scan.json()["discovered_files"] == 2

    status = client.get("/index/status")
    assert status.status_code == 200
    files = status.json()["files"]
    assert files["total"] == 2
    assert files["discovered"] == 2
    assert files["deleted"] == 0

    # Remove one file and rescan; file should be marked deleted.
    (data_dir / "readme.txt").unlink()
    rescan = client.post("/index/scan", json={"folder_id": folder_id})
    assert rescan.status_code == 200
    assert rescan.json()["marked_deleted_files"] == 1

    status2 = client.get("/index/status")
    assert status2.status_code == 200
    files2 = status2.json()["files"]
    assert files2["deleted"] == 1
