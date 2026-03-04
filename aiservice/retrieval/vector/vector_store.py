from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from retrieval.vector.embedder import embedder
from pathlib import Path
from core.config import settings

class VectorStore:
    """
    FAISS-backed vector store using LangChain.
    Products are embedded using MiniLM and stored as Documents.
    """
    def __init__(self):
        self.store = None
        self.path  = settings.FAISS_INDEX_PATH

    # ── Build from product list ───────────────────────────────────────────────
    def build(self, products: list):
        docs = [self._to_document(p) for p in products]
        self.store = FAISS.from_documents(docs, embedder.get())
        self._save()
        print(f"✅ FAISS vector store built: {len(docs)} products")

    # ── Persist and load ─────────────────────────────────────────────────────
    def _save(self):
        Path(self.path).mkdir(parents=True, exist_ok=True)
        self.store.save_local(self.path)
        print(f"💾 FAISS index saved to {self.path}")

    def load(self):
        self.store = FAISS.load_local(
            self.path,
            embedder.get(),
            allow_dangerous_deserialization=True,
        )
        print(f"📂 FAISS index loaded from {self.path}")

    # ── Semantic search ──────────────────────────────────────────────────────
    def search(
        self,
        query:  str,
        top_k:  int   = 5,
        budget: float = None,
        category: str = None,
        brand: str = None,
        features: list = None,
    ) -> list:
        if not self.store:
            return []

        # Over-fetch to allow filtering + relevance reranking.
        raw = self.store.similarity_search_with_score(query, k=max(top_k * 8, 20))
        query_lower = query.lower()
        category_lower = str(category or "").strip().lower()
        brand_lower = str(brand or "").strip().lower()
        feature_tokens = [
            str(f).strip().lower()
            for f in (features or [])
            if str(f).strip()
        ]

        results = []
        for doc, score in raw:
            p = doc.metadata.copy()
            if budget is not None and p.get("price", 0) > budget:
                continue

            p_category = str(p.get("category", "")).lower()
            p_brand = str(p.get("brand", "")).lower()
            p_text = (
                f"{p.get('name', '')} {p.get('description', '')} "
                f"{' '.join(p.get('features', []))}"
            ).lower()

            # Hard category filter only if the user clearly requested one.
            if category_lower and category_lower not in p_category:
                continue

            base = float(1 / (1 + score))
            bonus = 0.0

            if brand_lower and brand_lower == p_brand:
                bonus += 0.08

            matched_features = 0
            for token in feature_tokens:
                if token in p_text:
                    matched_features += 1
            if feature_tokens:
                bonus += min(matched_features / len(feature_tokens), 1.0) * 0.12

            # Small lexical bonus keeps semantic quality but reduces off-topic hits.
            lexical_hits = 0
            for token in query_lower.split():
                if len(token) < 3:
                    continue
                if token in p_text:
                    lexical_hits += 1
            bonus += min(lexical_hits / 8, 1.0) * 0.08

            p["vector_score"] = round(base + bonus, 4)
            results.append(p)

        results.sort(key=lambda x: x.get("vector_score", 0), reverse=True)
        return results[:top_k]

    # ── Convert product dict → LangChain Document ────────────────────────────
    def _to_document(self, p: dict) -> Document:
        content = (
            f"{p['name']} | category: {p['category']} | brand: {p['brand']} "
            f"| price: {p['price']} | features: {' '.join(p.get('features', []))} "
            f"| {p['description']}"
        )
        return Document(
            page_content=content,
            metadata={
                "id":          p["id"],
                "name":        p["name"],
                "price":       float(p["price"]),
                "category":    p["category"],
                "brand":       p["brand"],
                "rating":      float(p.get("rating", 0)),
                "stock":       int(p.get("stock", 0)),
                "description": p.get("description", ""),
                "features":    p.get("features", []),
            },
        )

vector_store = VectorStore()
