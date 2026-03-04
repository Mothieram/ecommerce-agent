import pandas as pd
from core.config import settings

class CSVLoader:
    def __init__(self):
        self.products = []
        self._loaded  = False

    def load(self, csv_path: str = None) -> list:
        path = csv_path or settings.CSV_PATH
        df   = pd.read_csv(path)
        df.fillna("", inplace=True)

        self.products = []
        for _, row in df.iterrows():
            features = [
                f.strip()
                for f in str(row.get("features", "")).split(",")
                if f.strip()
            ]
            self.products.append({
                "id":          str(int(row["id"])),
                "name":        str(row["name"]),
                "category":    str(row["category"]),
                "brand":       str(row["brand"]),
                "price":       float(row["price"]),
                "features":    features,
                "description": str(row["description"]),
                "rating":      float(row.get("rating", 0)),
                "stock":       int(row.get("stock", 0)),
            })

        self._loaded = True
        print(f"📦 Loaded {len(self.products)} products from CSV")
        return self.products

    def get_all(self) -> list:
        if not self._loaded:
            self.load()
        return self.products

    def get_categories(self) -> list:
        return list({p["category"] for p in self.get_all()})

    def get_brands(self) -> list:
        return list({p["brand"] for p in self.get_all()})

csv_loader = CSVLoader()
