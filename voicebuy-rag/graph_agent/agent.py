"""
LangGraph agent for VoiceBuy RAG.

Flow:
  detect_intent
      ↓
  extract_preferences
      ↓
  [route_after_preferences]
      ├── greeting → node_greeting → END
      └── * → vector_search
                  ↓
              [route_after_vector]
                  ├── has filters → graph_search → merge_results
                  └── no filters  → merge_results
                                        ↓
                                  generate_response → END
"""
from langgraph.graph import StateGraph, END
from graph_agent.state import AgentState
from graph_agent.nodes import (
    node_detect_intent,
    node_extract_preferences,
    node_vector_search,
    node_graph_search,
    node_merge_results,
    node_generate_response,
    node_greeting,
    node_error,
)
from graph_agent.edges import route_after_preferences, route_after_vector

def build_agent():
    wf = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────────
    wf.add_node("detect_intent",       node_detect_intent)
    wf.add_node("extract_preferences", node_extract_preferences)
    wf.add_node("vector_search",       node_vector_search)
    wf.add_node("graph_search",        node_graph_search)
    wf.add_node("merge_results",       node_merge_results)
    wf.add_node("generate_response",   node_generate_response)
    wf.add_node("greeting",            node_greeting)
    wf.add_node("error",               node_error)

    # ── Entry point ───────────────────────────────────────────────────────────
    wf.set_entry_point("detect_intent")

    # ── Fixed edges ───────────────────────────────────────────────────────────
    wf.add_edge("detect_intent",     "extract_preferences")
    wf.add_edge("graph_search",      "merge_results")
    wf.add_edge("merge_results",     "generate_response")
    wf.add_edge("generate_response", END)
    wf.add_edge("greeting",          END)
    wf.add_edge("error",             END)

    # ── Conditional edges ─────────────────────────────────────────────────────
    wf.add_conditional_edges(
        "extract_preferences",
        route_after_preferences,
        {
            "greeting":     "greeting",
            "vector_search":"vector_search",
        },
    )

    wf.add_conditional_edges(
        "vector_search",
        route_after_vector,
        {
            "graph_search":  "graph_search",
            "merge_results": "merge_results",
        },
    )

    return wf.compile()

# Singleton — compiled once on startup
voicebuy_agent = build_agent()
