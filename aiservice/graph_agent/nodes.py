"""
LangGraph nodes - each node performs one step in the agent pipeline.
All nodes receive the full AgentState and return an updated state.
"""
import asyncio
from graph_agent.state import AgentState
from chains.intent_chain import intent_chain
from chains.preference_chain import preference_chain
from chains.rag_chain import rag_chain
from retrieval.vector.vector_store import vector_store
from retrieval.graph.graph_store import graph_store
from dataset.product_store import product_store


async def node_detect_intent(state: AgentState) -> AgentState:
    intent = await intent_chain.detect(state["query"])
    print(f"  Intent  : {intent}")
    return {**state, "intent": intent}


async def node_extract_preferences(state: AgentState) -> AgentState:
    prefs = await preference_chain.extract(state["query"])
    print(f"  Prefs   : {prefs}")
    return {**state, "preferences": prefs}


async def node_vector_search(state: AgentState) -> AgentState:
    prefs = state.get("preferences") or {}
    results = vector_store.search(
        query=state["query"],
        top_k=8,
        budget=prefs.get("budget"),
        category=prefs.get("category"),
        brand=prefs.get("brand"),
        features=prefs.get("features"),
    )
    print(f"  Vector  : {len(results)} results")
    return {**state, "vector_results": results}


async def node_graph_search(state: AgentState) -> AgentState:
    prefs = state.get("preferences") or {}
    results = []
    budget = prefs.get("budget")
    category_pref = str(prefs.get("category") or "").strip().lower()

    tasks = []
    if prefs.get("category"):
        tasks.append(graph_store.search_by_category(prefs["category"], budget))
    if prefs.get("brand"):
        tasks.append(graph_store.search_by_brand(prefs["brand"]))
    if prefs.get("features"):
        tasks.append(graph_store.search_by_feature(prefs["features"]))

    if tasks:
        graph_batches = await asyncio.gather(*tasks, return_exceptions=True)
        for batch in graph_batches:
            if isinstance(batch, list):
                results.extend(batch)

    if results:
        seen_ids = {str(p.get("id")) for p in results if p.get("id") is not None}
        neighbor_tasks = []
        for p in results[:5]:
            pid = p.get("id")
            if pid is not None:
                neighbor_tasks.append(graph_store.get_similar_products(str(pid), top_k=3))

        expanded = []
        if neighbor_tasks:
            neighbor_batches = await asyncio.gather(*neighbor_tasks, return_exceptions=True)
            for batch in neighbor_batches:
                if not isinstance(batch, list):
                    continue
                for n in batch:
                    nid = str(n.get("id")) if n.get("id") is not None else None
                    if nid and nid not in seen_ids:
                        seen_ids.add(nid)
                        expanded.append(n)
        results.extend(expanded)

    if budget is not None:
        filtered = []
        for p in results:
            try:
                if float(p.get("price", 0)) <= float(budget):
                    filtered.append(p)
            except (TypeError, ValueError):
                continue
        results = filtered

    if category_pref:
        filtered = []
        for p in results:
            p_category = str(p.get("category", "")).strip().lower()
            if not p_category:
                full = product_store.get_by_id(str(p.get("id")))
                if full:
                    p_category = str(full.get("category", "")).strip().lower()
            if category_pref in p_category:
                filtered.append(p)
        results = filtered

    # Deduplicate after expansion/filtering.
    dedup = {}
    for p in results:
        pid = str(p.get("id"))
        if pid not in dedup:
            dedup[pid] = p
    results = list(dedup.values())

    print(f"  Graph   : {len(results)} results")
    return {**state, "graph_results": results}


async def node_merge_results(state: AgentState) -> AgentState:
    prefs = state.get("preferences") or {}
    pref_category = str(prefs.get("category") or "").strip().lower()
    pref_brand = str(prefs.get("brand") or "").strip().lower()
    pref_budget = prefs.get("budget")
    feature_tokens = [
        str(f).strip().lower()
        for f in (prefs.get("features") or [])
        if str(f).strip()
    ]

    merged = {}

    for p in (state.get("vector_results") or []):
        pid = p["id"]
        merged[pid] = p.copy()
        merged[pid]["final_score"] = p.get("vector_score", 0) * 0.6

    for p in (state.get("graph_results") or []):
        pid = p["id"]
        if pid in merged:
            merged[pid]["final_score"] += p.get("graph_score", 0) * 0.25
        else:
            p = p.copy()
            p["final_score"] = p.get("graph_score", 0) * 0.25
            merged[pid] = p

    ranked = sorted(
        merged.values(),
        key=lambda x: x.get("final_score", 0),
        reverse=True,
    )

    enriched = []
    for p in ranked[:5]:
        full = product_store.get_by_id(p["id"])
        if full:
            full["final_score"] = p.get("final_score", 0)
            enriched.append(full)
        else:
            enriched.append(p)

    # Final preference-aware rerank to improve precision.
    for p in enriched:
        score = float(p.get("final_score", 0))
        p_category = str(p.get("category", "")).lower()
        p_brand = str(p.get("brand", "")).lower()
        p_text = f"{p.get('name', '')} {p.get('description', '')} {' '.join(p.get('features', []))}".lower()

        if pref_category and pref_category in p_category:
            score += 0.15
        if pref_brand and pref_brand == p_brand:
            score += 0.08
        if feature_tokens:
            matched = sum(1 for token in feature_tokens if token in p_text)
            score += min(matched / len(feature_tokens), 1.0) * 0.12

        p["final_score"] = round(score, 5)

    # Enforce hard constraints from extracted preferences.
    # If the filtered set becomes empty, keep previous ranked list as fallback.
    constrained = enriched

    if pref_budget is not None:
        budget_filtered = []
        for p in constrained:
            try:
                if float(p.get("price", 0)) <= float(pref_budget):
                    budget_filtered.append(p)
            except (TypeError, ValueError):
                continue
        if budget_filtered:
            constrained = budget_filtered

    if pref_category:
        category_filtered = [
            p for p in constrained
            if pref_category in str(p.get("category", "")).strip().lower()
        ]
        if category_filtered:
            constrained = category_filtered

    if pref_brand:
        brand_filtered = [
            p for p in constrained
            if pref_brand == str(p.get("brand", "")).strip().lower()
        ]
        if brand_filtered:
            constrained = brand_filtered

    constrained.sort(key=lambda x: x.get("final_score", 0), reverse=True)
    enriched = constrained[:5]

    print(f"  Ranked  : {len(enriched)} products")
    return {**state, "final_products": enriched}


async def node_generate_response(state: AgentState) -> AgentState:
    response = await rag_chain.generate(
        query=state["query"],
        products=state.get("final_products") or [],
        intent=state.get("intent", "search"),
    )
    return {**state, "response": response}


async def node_greeting(state: AgentState) -> AgentState:
    return {
        **state,
        "response": "Hello! I'm VoiceBuy AI. How can I help you shop today? "
                    "Try asking me to find products, compare items, or get recommendations!",
        "final_products": [],
        "action_taken": "greeting",
    }


async def node_error(state: AgentState) -> AgentState:
    return {
        **state,
        "response": "Sorry, something went wrong. Please try again.",
        "action_taken": "error",
        "error": "pipeline_error",
    }
