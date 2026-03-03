from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_huggingface import HuggingFacePipeline
from llm.gemma_client import gemma_client

INTENT_PROMPT = PromptTemplate(
    input_variables=["query"],
    template="""<start_of_turn>user
You are a shopping assistant. Classify the user's query into exactly ONE intent.

Intents:
- search      → user wants to find or browse products
- compare     → user wants to compare two or more products
- add_cart    → user wants to add a product to cart
- remove_cart → user wants to remove a product from cart
- recommend   → user wants a recommendation or suggestion
- greeting    → user is saying hello or starting conversation
- unknown     → cannot classify

Query: {query}

Reply with ONLY the intent word, nothing else.<end_of_turn>
<start_of_turn>model
"""
)

VALID_INTENTS = [
    "search", "compare", "add_cart", "remove_cart",
    "recommend", "greeting", "unknown"
]

class IntentChain:
    def __init__(self):
        self.chain = None

    def build(self):
        self.chain = INTENT_PROMPT | gemma_client.get_llm() | StrOutputParser()
        print("✅ Intent chain ready")

    async def detect(self, query: str) -> str:
        raw    = await self.chain.ainvoke({"query": query})
        intent = raw.strip().lower().split()[0] if raw.strip() else "search"
        return intent if intent in VALID_INTENTS else "search"

intent_chain = IntentChain()