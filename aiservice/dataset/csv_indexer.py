"""
Orchestrates loading CSV and building FAISS + Neo4j indexes.
Rebuilds FAISS when the CSV has changed.
"""
from pathlib import Path
from dataset.csv_loader import csv_loader
from dataset.product_store import product_store
from retrieval.vector.vector_store import vector_store
from retrieval.graph.graph_builder import graph_builder
from core.config import settings


class CSVIndexer:
    def __init__(self):
        self.faiss_path = Path(settings.FAISS_INDEX_PATH) / "index.faiss"
        self.csv_path = Path(settings.CSV_PATH)

    async def run(self):
        # Step 1: Load CSV into memory
        products = csv_loader.load()

        # Step 2: Fill in-memory product store
        product_store.load(products)

        # Step 3: Build or load FAISS vector index
        if self._should_rebuild_faiss():
            print("Building FAISS index from CSV products...")
            vector_store.build(products)
        else:
            print("FAISS index found and up-to-date; loading from disk...")
            vector_store.load()

        # Step 4: Build Neo4j graph from CSV products
        print("Building Neo4j knowledge graph...")
        await graph_builder.build_from_products(products)

        print("All indexes ready")

    def _should_rebuild_faiss(self) -> bool:
        """
        Rebuild when FAISS index is missing or older than CSV.
        """
        if not self.faiss_path.exists():
            return True
        if not self.csv_path.exists():
            return False
        return self.csv_path.stat().st_mtime > self.faiss_path.stat().st_mtime


csv_indexer = CSVIndexer()
