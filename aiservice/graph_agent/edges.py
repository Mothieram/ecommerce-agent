from graph_agent.state import AgentState

def route_after_preferences(state: AgentState) -> str:
    """
    After extracting intent + preferences, decide which path to take.

    Routing logic:
      greeting         → node_greeting        (skip retrieval)
      search/recommend → vector_search        (do full retrieval)
      compare          → vector_search        (do full retrieval)
      unknown          → vector_search        (try retrieval anyway)
    """
    intent = state.get("intent", "search")

    if intent == "greeting":
        return "greeting"

    return "vector_search"

def route_after_vector(state: AgentState) -> str:
    """
    After vector search, decide if graph search is also needed.

    Do graph search if any structural filter is present:
      - category, brand, or features extracted from preferences
    """
    prefs = state.get("preferences") or {}

    has_structure = (
        prefs.get("category")
        or prefs.get("brand")
        or prefs.get("features")
    )

    return "graph_search" if has_structure else "merge_results"
