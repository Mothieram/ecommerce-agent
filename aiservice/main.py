from fastapi import FastAPI
from api.router import router
from core.startup import startup_event, shutdown_event

app = FastAPI(
    title       = "VoiceBuy RAG API",
    description = """
Standalone Agentic RAG service powered by:
- **LangGraph** — agent orchestration
- **LangChain** — LLM chains
- **Gemma 1B**  — intent + preference extraction + RAG generation
- **FAISS**     — vector / semantic search
- **Neo4j**     — knowledge graph search
- **CSV**       — product data source (no Django / no DB needed)
    """,
    version = "1.0.0",
)

@app.on_event("startup")
async def on_startup():
    await startup_event()

@app.on_event("shutdown")
async def on_shutdown():
    await shutdown_event()

app.include_router(router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok", "mode": "CSV-only RAG"}

@app.get("/")
def root():
    return {
        "message": "VoiceBuy RAG is running!",
        "docs":    "http://localhost:8001/docs",
        "health":  "http://localhost:8001/health",
    }
