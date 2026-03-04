from collections import defaultdict
from retrieval.graph.graph_store import graph_store


class GraphBuilder:
    """Builds the Neo4j knowledge graph from a list of product dicts."""

    async def build_from_products(self, products: list):
        await graph_store.clear_all()

        for p in products:
            await graph_store.add_product(p)

        edge_pairs = self._collect_similarity_edges(products)
        await graph_store.add_similarity_edges(edge_pairs)
        print(f"Neo4j graph built: {len(products)} products, {len(edge_pairs)} similarity pairs")

    def _collect_similarity_edges(self, products: list) -> list:
        """
        Connect products in same category with close price (within 30%)
        as SIMILAR_TO relationships.

        Uses category bucketing + sorted prices so this scales better than
        a full O(n^2) global comparison.
        """
        by_category = defaultdict(list)
        for p in products:
            by_category[p.get("category", "")].append(p)

        pair_set = set()
        for items in by_category.values():
            items = sorted(items, key=lambda x: float(x.get("price", 0)))
            if len(items) < 2:
                continue

            for i, p1 in enumerate(items):
                price1 = float(p1.get("price", 0))
                if price1 <= 0:
                    continue

                # Always connect to nearest next product in same category
                if i + 1 < len(items):
                    pair_set.add((p1["id"], items[i + 1]["id"]))

                j = i + 2
                while j < len(items):
                    p2 = items[j]
                    price2 = float(p2.get("price", 0))
                    avg = (price1 + price2) / 2
                    diff = abs(price1 - price2)
                    ratio = (diff / avg) if avg else 1

                    if ratio < 0.35:
                        pair_set.add((p1["id"], p2["id"]))
                        j += 1
                        continue

                    # Prices are sorted ascending; once ratio breaks for higher prices,
                    # it will only get worse for the current p1.
                    break

        return list(pair_set)


graph_builder = GraphBuilder()
