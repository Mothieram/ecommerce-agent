from typing import TypedDict, Optional, List

class AgentState(TypedDict):
    # ── Input ────────────────────────────────────────────────────────────────
    query:   str
    user_id: str

    # ── Extracted by Gemma 1B chains ─────────────────────────────────────────
    intent:      Optional[str]
    preferences: Optional[dict]

    # ── Retrieval results ─────────────────────────────────────────────────────
    vector_results: Optional[List[dict]]
    graph_results:  Optional[List[dict]]
    final_products: Optional[List[dict]]

    # ── Output ────────────────────────────────────────────────────────────────
    response:     Optional[str]
    action_taken: Optional[str]
    error:        Optional[str]
