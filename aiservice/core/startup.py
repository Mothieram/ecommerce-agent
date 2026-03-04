from dataset.csv_indexer import csv_indexer
from retrieval.graph.graph_store import graph_store
from llm.gemma_client import gemma_client
from chains.intent_chain import intent_chain
from chains.preference_chain import preference_chain
from chains.rag_chain import rag_chain


async def startup_event():
    print("Starting VoiceBuy RAG Service (CSV Mode)...")

    # Step 1: Load Gemma 1B
    gemma_client.load()

    # Step 2: Build LangChain chains
    intent_chain.build()
    preference_chain.build()
    rag_chain.build()

    # Step 3: Connect Neo4j
    await graph_store.connect()

    # Step 4: Load CSV and build indexes
    await csv_indexer.run()

    print("VoiceBuy RAG is ready")
    print("Swagger UI -> http://localhost:8000/docs")


async def shutdown_event():
    await graph_store.close()
    print("Shutdown complete")
