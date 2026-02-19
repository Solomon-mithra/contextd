import os
from typing import List, Optional, Tuple

import psycopg


DEFAULT_DB_URL = "postgresql://contextd:contextd@localhost:5433/contextd"


def get_db_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DB_URL)


def _to_pgvector_literal(vec: List[float]) -> str:
    # pgvector accepts string literal like: "[0.1,0.2,0.3]"
    # We keep it compact and deterministic.
    return "[" + ",".join(f"{x:.8f}" for x in vec) + "]"


def search_chunks(
    query_embedding: List[float],
    limit: int = 5,
    probes: Optional[int] = None,
) -> List[Tuple[int, str, float]]:
    """
    Returns: (chunk_id, chunk_content, distance)
    """
    if len(query_embedding) != 768:
        raise ValueError(f"Expected embedding length 768, got {len(query_embedding)}")

    qv = _to_pgvector_literal(query_embedding)

    sql_set_probes = "SET ivfflat.probes = %s;" if probes is not None else None

    sql = """
        SELECT id, content, (embedding <=> (%s::vector)) AS distance
        FROM chunks
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> (%s::vector)
        LIMIT %s;
    """

    with psycopg.connect(get_db_url()) as conn:
        with conn.cursor() as cur:
            if sql_set_probes is not None:
                cur.execute(sql_set_probes, (probes,))
            cur.execute(sql, (qv, qv, limit))
            rows = cur.fetchall()
            return [(int(r[0]), str(r[1]), float(r[2])) for r in rows]