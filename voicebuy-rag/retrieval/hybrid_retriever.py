"""
Hybrid retriever: combines FAISS vector search + Neo4j graph search.

Scoring formula:
  final_score = (vector_score × 0.6) + (graph_score × 0.4)
"""
from retrieval.vector.vector_store import vector_store
from retrieval.graph.graph_store import graph_store

VECTOR_WEIGHT = 0.6
GRAPH_WEIGHT  = 0.4

class HybridRetriever:

    async def retrieve(
        self,
        query:    str,
        budget:   float = None,
        category: str   = None,
        brand:    str   = None,
        features: list  = None,
        top_k:    int   = 5,
    ) -> list:

        merged = {}   # product id → product with scores

        # ── 1. Vector search (semantic) ───────────────────────────────────────
        vector_results = vector_store.search(query, top_k=top_k * 2, budget=budget)
        for p in vector_results:
            pid = p["id"]
            merged[pid] = p.copy()
            merged[pid]["final_score"] = p.get("vector_score", 0) * VECTOR_WEIGHT

        # ── 2. Graph search (structural) ─────────────────────────────────────

        # 2a: Category filter
        if category:
            cat_results = await graph_store.search_by_category(
                category, budget, top_k
            )
            self._merge(merged, cat_results, GRAPH_WEIGHT)

        # 2b: Brand filter
        if brand:
            brand_results = await graph_store.search_by_brand(brand, top_k)
            self._merge(merged, brand_results, GRAPH_WEIGHT)

        # 2c: Feature filter
        if features:
            feat_results = await graph_store.search_by_feature(features, top_k)
            self._merge(merged, feat_results, GRAPH_WEIGHT)

        # ── 3. Sort by final score ────────────────────────────────────────────
        ranked = sorted(
            merged.values(),
            key=lambda x: x.get("final_score", 0),
            reverse=True,
        )

        return ranked[:top_k]

    def _merge(self, merged: dict, new_results: list, weight: float):
        """Add graph results into merged dict, boosting score if already present."""
        for p in new_results:
            pid = p["id"]
            if pid in merged:
                merged[pid]["final_score"] += p.get("graph_score", 0) * weight
            else:
                p = p.copy()
                p["final_score"] = p.get("graph_score", 0) * weight
                merged[pid] = p

hybrid_retriever = HybridRetriever()
