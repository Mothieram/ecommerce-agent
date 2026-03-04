"""
In-memory product store — replaces a real database during CSV-only mode.
Acts as a fast lookup dictionary after CSV is loaded.
"""

class ProductStore:
    def __init__(self):
        self.products:     dict = {}   # id -> product dict
        self.by_category:  dict = {}   # category -> [products]
        self.by_brand:     dict = {}   # brand -> [products]

    def load(self, products: list):
        self.products    = {}
        self.by_category = {}
        self.by_brand    = {}

        for p in products:
            pid = p["id"]
            self.products[pid] = p

            cat = p["category"]
            self.by_category.setdefault(cat, []).append(p)

            brand = p["brand"]
            self.by_brand.setdefault(brand, []).append(p)

        print(f"🗂️  ProductStore: {len(self.products)} products indexed")

    def get_by_id(self, pid: str) -> dict:
        return self.products.get(str(pid))

    def get_all(self) -> list:
        return list(self.products.values())

    def get_by_category(self, category: str) -> list:
        category_lower = category.lower()
        results = []
        for cat, products in self.by_category.items():
            if category_lower in cat.lower():
                results.extend(products)
        return results

    def get_by_brand(self, brand: str) -> list:
        brand_lower = brand.lower()
        results = []
        for b, products in self.by_brand.items():
            if brand_lower in b.lower():
                results.extend(products)
        return results

    def filter_by_budget(self, products: list, budget: float) -> list:
        return [p for p in products if p["price"] <= budget]

    def search_by_name(self, query: str) -> list:
        query_lower = query.lower()
        return [
            p for p in self.get_all()
            if query_lower in p["name"].lower()
            or query_lower in p["description"].lower()
        ]

product_store = ProductStore()
