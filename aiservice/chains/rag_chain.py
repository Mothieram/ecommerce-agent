from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from llm.gemma_client import gemma_client

RAG_PROMPT = PromptTemplate(
    input_variables=["query", "intent", "products"],
    template="""<start_of_turn>user
You are VoiceBuy AI, a helpful Amazon shopping assistant.

User Intent : {intent}
User Query  : {query}

Top matching products from our catalog:
{products}

Instructions:
- search / recommend → suggest the best 1-2 products with clear reasons
- compare            → highlight key differences in price, rating, features
- Keep response under 80 words
- Always mention product name and price ($)
- Be friendly and specific<end_of_turn>
<start_of_turn>model
"""
)

class RAGChain:
    def __init__(self):
        self.chain = None

    def build(self):
        self.chain = RAG_PROMPT | gemma_client.get_llm() | StrOutputParser()
        print("✅ RAG chain ready")

    async def generate(self, query: str, products: list,
                        intent: str) -> str:
        if not products:
            return "Sorry, I couldn't find any matching products. Please try a different search."

        # Fast deterministic path for common shopping intents.
        if intent in {"search", "recommend"}:
            top = products[:2]
            if len(top) == 1:
                p = top[0]
                return (
                    f"I recommend {p['name']} (${p['price']:.2f}). "
                    f"It has a {p.get('rating', 'N/A')} rating and key features: "
                    f"{', '.join((p.get('features') or [])[:3])}."
                )
            p1, p2 = top[0], top[1]
            return (
                f"Top picks: {p1['name']} (${p1['price']:.2f}) and "
                f"{p2['name']} (${p2['price']:.2f}). "
                f"{p1['name']} is rated {p1.get('rating', 'N/A')}, while "
                f"{p2['name']} is rated {p2.get('rating', 'N/A')}. "
                "Want a quick comparison on camera, battery, or performance?"
            )

        lines = []
        for i, p in enumerate(products[:4]):
            discount = f" [{p['discount']}]" if p.get("discount") else ""
            reviews  = f"| {p.get('reviews_count', 0):,} reviews" if p.get("reviews_count") else ""
            lines.append(
                f"{i+1}. {p['name'][:60]}"
                f" | ${p['price']:.2f}{discount}"
                f" | Rating: {p.get('rating', 'N/A')}{reviews}"
                f" | Brand: {p.get('brand', '')}"
            )

        product_text = "\n".join(lines)
        result = await self.chain.ainvoke({
            "query":    query,
            "intent":   intent,
            "products": product_text,
        })
        return result.strip()

rag_chain = RAGChain()
