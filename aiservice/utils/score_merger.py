def merge_and_rank(
    vector_results: list,
    graph_results:  list,
    vector_weight:  float = 0.6,
    graph_weight:   float = 0.4,
    top_k:          int   = 5,
) -> list:
    """
    Merge vector and graph results using weighted score fusion.
    Products present in both lists get a boosted final score.
    """
    merged = {}

    for p in vector_results:
        pid = p["id"]
        merged[pid] = p.copy()
        merged[pid]["final_score"] = p.get("vector_score", 0) * vector_weight

    for p in graph_results:
        pid = p["id"]
        if pid in merged:
            merged[pid]["final_score"] += p.get("graph_score", 0) * graph_weight
        else:
            p = p.copy()
            p["final_score"] = p.get("graph_score", 0) * graph_weight
            merged[pid] = p

    ranked = sorted(
        merged.values(),
        key=lambda x: x.get("final_score", 0),
        reverse=True,
    )
    return ranked[:top_k]
