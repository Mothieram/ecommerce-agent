import asyncio
from neo4j import AsyncGraphDatabase
from neo4j.exceptions import Neo4jError, ServiceUnavailable, SessionExpired
from core.config import settings


class GraphStore:
    """
    Neo4j graph store.

    Graph schema:
      (Product)-[:BELONGS_TO]->(Category)
      (Product)-[:MADE_BY]->(Brand)
      (Product)-[:HAS_FEATURE]->(Feature)
      (Product)-[:SIMILAR_TO]->(Product)
    """

    def __init__(self):
        self.driver = None

    async def connect(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            max_connection_lifetime=180,
        )
        try:
            await self.driver.verify_connectivity()
            await self._ensure_schema()
            print("Neo4j connected")
        except Exception as exc:
            print(f"Neo4j connectivity check failed: {exc}")

    async def _ensure_schema(self):
        schema_queries = [
            "CREATE CONSTRAINT product_id_unique IF NOT EXISTS FOR (p:Product) REQUIRE p.id IS UNIQUE",
            "CREATE INDEX category_name_idx IF NOT EXISTS FOR (c:Category) ON (c.name)",
            "CREATE INDEX brand_name_idx IF NOT EXISTS FOR (b:Brand) ON (b.name)",
            "CREATE INDEX feature_name_idx IF NOT EXISTS FOR (f:Feature) ON (f.name)",
            "CREATE INDEX product_price_idx IF NOT EXISTS FOR (p:Product) ON (p.price)",
        ]
        for q in schema_queries:
            await self._safe_run(q, retries=0)

    async def close(self):
        if self.driver:
            await self.driver.close()

    async def _safe_run(self, query: str, params: dict = None, retries: int = 2):
        """
        Execute Cypher with transient network retries.
        Returns [] on failure so API can degrade gracefully.
        """
        if not self.driver:
            return []

        params = params or {}
        for attempt in range(retries + 1):
            try:
                async with self.driver.session() as s:
                    result = await s.run(query, **params)
                    return await result.data()
            except (ServiceUnavailable, SessionExpired, ConnectionError, OSError) as exc:
                if attempt >= retries:
                    print(f"Neo4j transient failure after retries: {exc}")
                    return []
                await asyncio.sleep(0.2 * (attempt + 1))
            except Neo4jError as exc:
                print(f"Neo4j query error: {exc}")
                return []
            except Exception as exc:
                print(f"Unexpected Neo4j error: {exc}")
                return []

        return []

    async def clear_all(self):
        await self._safe_run("MATCH (n) DETACH DELETE n")

    async def add_product(self, p: dict):
        query = """
            MERGE (prod:Product {id: $id})
            SET   prod.name   = $name,
                  prod.price  = $price,
                  prod.rating = $rating,
                  prod.stock  = $stock

            MERGE (cat:Category {name: $category})
            MERGE (brd:Brand    {name: $brand})

            MERGE (prod)-[:BELONGS_TO]->(cat)
            MERGE (prod)-[:MADE_BY]->(brd)
        """
        await self._safe_run(
            query,
            {
                "id": p["id"],
                "name": p["name"],
                "price": float(p["price"]),
                "rating": float(p.get("rating", 0)),
                "stock": int(p.get("stock", 0)),
                "category": p.get("category", ""),
                "brand": p.get("brand", ""),
            },
        )

        for feat in p.get("features", []):
            feat = feat.strip()
            if not feat:
                continue
            await self._safe_run(
                """
                MATCH (prod:Product {id: $id})
                MERGE (f:Feature {name: $feat})
                MERGE (prod)-[:HAS_FEATURE]->(f)
                """,
                {"id": p["id"], "feat": feat},
            )

    async def add_similarity_edge(self, id1: str, id2: str):
        await self._safe_run(
            """
            MATCH (p1:Product {id: $id1})
            MATCH (p2:Product {id: $id2})
            MERGE (p1)-[:SIMILAR_TO]->(p2)
            MERGE (p2)-[:SIMILAR_TO]->(p1)
            """,
            {"id1": id1, "id2": id2},
        )

    async def add_similarity_edges(self, pairs: list):
        """
        Bulk create bidirectional SIMILAR_TO edges.
        `pairs` is a list of tuples: [(id1, id2), ...]
        """
        if not pairs:
            return

        rows = [{"id1": id1, "id2": id2} for id1, id2 in pairs]
        await self._safe_run(
            """
            UNWIND $rows AS row
            MATCH (p1:Product {id: row.id1})
            MATCH (p2:Product {id: row.id2})
            MERGE (p1)-[:SIMILAR_TO]->(p2)
            MERGE (p2)-[:SIMILAR_TO]->(p1)
            """,
            {"rows": rows},
        )

    async def search_by_category(
        self,
        category: str,
        budget: float = None,
        top_k: int = 5,
    ) -> list:
        query = """
            MATCH (p:Product)-[:BELONGS_TO]->(c:Category)
            WHERE toLower(c.name) CONTAINS toLower($category)
        """
        if budget is not None:
            query += " AND p.price <= $budget"
        query += " RETURN p ORDER BY p.rating DESC LIMIT $top_k"

        records = await self._safe_run(
            query,
            {"category": category, "budget": budget, "top_k": top_k},
        )
        return [{**dict(r["p"]), "graph_score": 0.85} for r in records if "p" in r]

    async def search_by_brand(
        self,
        brand: str,
        top_k: int = 5,
    ) -> list:
        records = await self._safe_run(
            """
            MATCH (p:Product)-[:MADE_BY]->(b:Brand)
            WHERE toLower(b.name) CONTAINS toLower($brand)
            RETURN p ORDER BY p.rating DESC LIMIT $top_k
            """,
            {"brand": brand, "top_k": top_k},
        )
        return [{**dict(r["p"]), "graph_score": 0.80} for r in records if "p" in r]

    async def search_by_feature(
        self,
        features: list,
        top_k: int = 5,
    ) -> list:
        if not features:
            return []

        norm_features = [str(f).strip().lower() for f in features if str(f).strip()]
        if not norm_features:
            return []

        records = await self._safe_run(
            """
            MATCH (p:Product)-[:HAS_FEATURE]->(f:Feature)
            WHERE any(x IN $features WHERE toLower(f.name) CONTAINS x OR x CONTAINS toLower(f.name))
            RETURN p, count(f) AS match_count
            ORDER BY match_count DESC, p.rating DESC
            LIMIT $top_k
            """,
            {"features": norm_features, "top_k": top_k},
        )

        size = max(len(norm_features), 1)
        return [
            {
                **dict(r["p"]),
                "graph_score": min(float(r.get("match_count", 0)) / size, 1.0),
            }
            for r in records
            if "p" in r
        ]

    async def get_similar_products(
        self,
        product_id: str,
        top_k: int = 5,
    ) -> list:
        records = await self._safe_run(
            """
            MATCH (p:Product {id: $pid})-[:SIMILAR_TO]->(sim:Product)
            RETURN sim ORDER BY sim.rating DESC LIMIT $top_k
            """,
            {"pid": product_id, "top_k": top_k},
        )
        return [{**dict(r["sim"]), "graph_score": 0.75} for r in records if "sim" in r]


graph_store = GraphStore()
