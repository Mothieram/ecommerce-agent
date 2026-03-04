from fastapi import APIRouter
from collections import OrderedDict
from models.schemas import VoiceRequest, VoiceResponse
from graph_agent.agent import voicebuy_agent

router = APIRouter()
_QUERY_CACHE = OrderedDict()
_CACHE_LIMIT = 200

@router.post("/query", response_model=VoiceResponse)
async def voice_query(req: VoiceRequest):
    """
    Main endpoint — runs the full LangGraph Agentic RAG pipeline.

    Steps inside agent:
      1. Detect intent (Gemma 1B)
      2. Extract preferences (Gemma 1B)
      3. Vector search (FAISS)
      4. Graph search (Neo4j) — if category/brand/features found
      5. Merge & rank results
      6. Generate response (Gemma 1B RAG)
    """
    initial_state = {
        "query":          req.text,
        "user_id":        req.user_id,
        "intent":         None,
        "preferences":    None,
        "vector_results": None,
        "graph_results":  None,
        "final_products": None,
        "response":       None,
        "action_taken":   None,
        "error":          None,
    }

    print(f"\n─── New Query ──────────────────────────────────")
    print(f"  📝 Query   : {req.text}")

    cache_key = f"{(req.text or '').strip().lower()}|{(req.user_id or '').strip().lower()}"
    if cache_key in _QUERY_CACHE:
        result = _QUERY_CACHE[cache_key]
        _QUERY_CACHE.move_to_end(cache_key)
    else:
        result = await voicebuy_agent.ainvoke(initial_state)
        _QUERY_CACHE[cache_key] = result
        _QUERY_CACHE.move_to_end(cache_key)
        while len(_QUERY_CACHE) > _CACHE_LIMIT:
            _QUERY_CACHE.popitem(last=False)

    print(f"  💬 Response: {result['response'][:60]}...")
    print(f"───────────────────────────────────────────────\n")

    return VoiceResponse(
        query       = result["query"],
        intent      = result.get("intent") or "unknown",
        preferences = result.get("preferences") or {},
        reply       = result.get("response") or "",
        products    = result.get("final_products") or [],
        action_taken= result.get("action_taken") or "none",
    )
