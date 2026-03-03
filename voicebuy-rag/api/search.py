from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from retrieval.vector.vector_store import vector_store
from retrieval.graph.graph_store import graph_store
from retrieval.hybrid_retriever import hybrid_retriever
from dataset.product_store import product_store

router = APIRouter()

class SearchRequest(BaseModel):
    query:    str
    budget:   Optional[float] = None
    category: Optional[str]   = None
    brand:    Optional[str]   = None
    top_k:    Optional[int]   = 5

@router.post("/vector")
async def vector_search(req: SearchRequest):
    """Direct FAISS vector search — no agent, no LLM."""
    results = vector_store.search(req.query, req.top_k, req.budget)
    return {"results": results, "count": len(results)}

@router.post("/graph")
async def graph_search(req: SearchRequest):
    """Direct Neo4j graph search — no agent, no LLM."""
    results = []
    if req.category:
        results += await graph_store.search_by_category(
            req.category, req.budget, req.top_k
        )
    if req.brand:
        results += await graph_store.search_by_brand(req.brand, req.top_k)
    return {"results": results, "count": len(results)}

@router.post("/hybrid")
async def hybrid_search(req: SearchRequest):
    """Hybrid vector + graph search — no agent, no LLM."""
    results = await hybrid_retriever.retrieve(
        query    = req.query,
        budget   = req.budget,
        category = req.category,
        brand    = req.brand,
        top_k    = req.top_k,
    )
    return {"results": results, "count": len(results)}

@router.get("/products")
async def list_products():
    """List all products from in-memory CSV store."""
    return {"products": product_store.get_all(), "count": len(product_store.products)}

@router.get("/products/{product_id}")
async def get_product(product_id: str):
    """Get a single product by ID."""
    p = product_store.get_by_id(product_id)
    if not p:
        return {"error": "Product not found"}
    return p
