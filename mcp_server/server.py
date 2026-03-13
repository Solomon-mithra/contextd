import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Claude Desktop may launch the stdio server without a writable repo cwd.
# Pin the DB path to an absolute location inside this repo for MCP usage.
os.environ.setdefault("RELEVECT_DB_PATH", str(ROOT / "data" / "relevect.db"))

from mcp.server.fastmcp import FastMCP

mcp = FastMCP(
    "relevect",
    instructions=(
        "Search the local indexed Relevect corpus and return passages with provenance metadata. "
        "This MCP server is search-only and does not manage indexing."
    ),
    log_level="ERROR",
)


@mcp.tool(
    name="search",
    description="Search indexed chunks in the local Relevect corpus and return passages with provenance metadata.",
)
def search(
    query: str,
    top_k: int = 5,
    include_text: bool = True,
    min_score: float | None = None,
) -> dict[str, Any]:
    from core.db import init_db, search_chunks
    from core.embeddings import embed_text, get_embedding_model_name

    query = query.strip()
    if not query:
        raise ValueError("query must be a non-empty string")
    if top_k < 1 or top_k > 20:
        raise ValueError("top_k must be between 1 and 20")

    init_db()
    query_embedding = embed_text(query)
    model_name = get_embedding_model_name()
    results = search_chunks(
        query,
        query_embedding,
        embedding_model=model_name,
        top_k=top_k,
        min_score=min_score,
    )

    if not include_text:
        results = [{**result, "text": None} for result in results]

    return {
        "query": query,
        "embedding_model": model_name,
        "results": results,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
