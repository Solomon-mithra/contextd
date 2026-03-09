import os
from dataclasses import dataclass
from pathlib import Path


SUPPORTED_EXTENSIONS = {".pdf", ".md", ".txt"}
IGNORED_DIR_NAMES = {".git", "__pycache__", "node_modules", ".venv"}


@dataclass(frozen=True)
class DiscoveredFile:
    path: str
    file_name: str
    extension: str
    size_bytes: int
    mtime: float


def _is_hidden_path(path: Path) -> bool:
    return any(part.startswith(".") for part in path.parts)


def discover_files(folder_path: str) -> list[DiscoveredFile]:
    """Discover supported files recursively under a folder path."""
    base = Path(folder_path)
    if not base.exists() or not base.is_dir():
        return []

    discovered: list[DiscoveredFile] = []

    for root, dirnames, filenames in os.walk(base):
        dirnames[:] = [
            d for d in dirnames if d not in IGNORED_DIR_NAMES and not d.startswith(".")
        ]

        root_path = Path(root)
        if _is_hidden_path(root_path.relative_to(base)):
            continue

        for name in filenames:
            if name.startswith(".") or name.endswith("~"):
                continue

            file_path = root_path / name
            ext = file_path.suffix.lower()
            if ext not in SUPPORTED_EXTENSIONS:
                continue

            try:
                stat = file_path.stat()
            except FileNotFoundError:
                # File can vanish between os.walk and stat; ignore and continue.
                continue

            discovered.append(
                DiscoveredFile(
                    path=str(file_path.resolve()),
                    file_name=name,
                    extension=ext,
                    size_bytes=int(stat.st_size),
                    mtime=float(stat.st_mtime),
                )
            )

    return discovered
