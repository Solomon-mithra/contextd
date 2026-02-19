from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.db import search_chunks

app = FastAPI()


class SearchRequest(BaseModel):
    embedding: List[float] = Field(..., description="Query embedding vector length 768")
    limit: int = Field(5, ge=1, le=50)
    probes: Optional[int] = Field(None, ge=1, le=200)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/search")
def search(req: SearchRequest):
    try:
        results = search_chunks(req.embedding, limit=req.limit, probes=req.probes)
        return {
            "results": [
                {"chunk_id": cid, "content": content, "distance": dist}
                for (cid, content, dist) in results
            ]
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))