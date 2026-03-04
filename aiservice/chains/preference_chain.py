from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from llm.gemma_client import gemma_client
import json
import re

PREF_PROMPT = PromptTemplate(
    input_variables=["query"],
    template="""<start_of_turn>user
Extract shopping preferences from the user query. Return ONLY valid JSON, no explanation.

JSON format:
{{
  "budget": <number in USD or null>,
  "category": <Amazon root category string or null>,
  "brand": <brand name or null>,
  "features": [<list of feature keywords>],
  "discount_only": <true if user wants deals/discounts, else false>
}}

Examples:
Query: "Nike running shoes under $100"
Output: {{"budget": 100, "category": "Clothing, Shoes & Jewelry", "brand": "Nike", "features": ["running"], "discount_only": false}}

Query: "best deals on kitchen tools"
Output: {{"budget": null, "category": "Home & Kitchen", "brand": null, "features": ["kitchen"], "discount_only": true}}

Query: "Accutire tire pressure gauge"
Output: {{"budget": null, "category": "Automotive", "brand": "Accutire", "features": ["tire pressure"], "discount_only": false}}

Query: {query}
Output:<end_of_turn>
<start_of_turn>model
"""
)

class PreferenceChain:
    def __init__(self):
        self.chain = None

    def build(self):
        self.chain = PREF_PROMPT | gemma_client.get_llm() | StrOutputParser()
        print("✅ Preference chain ready")

    async def extract(self, query: str) -> dict:
        raw   = await self.chain.ainvoke({"query": query})
        match = re.search(r'\{.*?\}', raw, re.DOTALL)
        if match:
            try:
                prefs = json.loads(match.group())
                return self._normalize_preferences(query, prefs)
            except json.JSONDecodeError:
                pass
        return self._normalize_preferences(query, {
            "budget":        None,
            "category":      None,
            "brand":         None,
            "features":      [],
            "discount_only": False,
        })

    def _normalize_preferences(self, query: str, prefs: dict) -> dict:
        """
        Normalize LLM output types and backfill budget using regex if LLM misses it.
        """
        if not isinstance(prefs, dict):
            prefs = {}

        budget = prefs.get("budget")
        if isinstance(budget, str):
            cleaned = budget.replace(",", "").strip()
            try:
                budget = float(cleaned)
            except ValueError:
                budget = None

        if budget is None:
            budget = self._extract_budget_from_query(query)

        query_lower = query.lower()

        category = prefs.get("category")
        brand = prefs.get("brand")
        features = prefs.get("features") or []

        if isinstance(brand, str) and brand.strip():
            if brand.lower() not in query_lower:
                brand = None
        else:
            brand = None

        inferred_category = self._infer_category_from_query(query_lower)
        if inferred_category:
            category = inferred_category
        elif isinstance(category, str) and category.strip().lower() in {"electronics", "product", "products"}:
            category = None

        cleaned_features = []
        stop_features = {"product", "products", "electronics", "smartphone", "smartphones", "phone", "mobile"}
        for f in features:
            token = str(f).strip().lower()
            if token and token not in stop_features:
                cleaned_features.append(token)

        prefs["budget"] = budget
        prefs["category"] = category
        prefs["brand"] = brand
        prefs["features"] = cleaned_features
        prefs["discount_only"] = bool(prefs.get("discount_only", False))
        return prefs

    def _infer_category_from_query(self, query_lower: str):
        category_map = {
            "smartphone": "Smartphones",
            "smartphones": "Smartphones",
            "mobile": "Smartphones",
            "mobiles": "Smartphones",
            "laptop": "Laptops",
            "laptops": "Laptops",
            "tv": "TVs",
            "tvs": "TVs",
            "tablet": "Tablets",
            "tablets": "Tablets",
            "headphone": "Audio",
            "headphones": "Audio",
            "earbuds": "Audio",
            "camera": "Cameras",
            "cameras": "Cameras",
            "router": "Networking",
            "routers": "Networking",
        }
        for key, value in category_map.items():
            if key in query_lower:
                return value
        return None

    def _extract_budget_from_query(self, query: str):
        q = query.lower().replace(",", "")

        patterns = [
            r"(?:under|below|less than|upto|up to|within|max(?:imum)?(?: budget)?(?: of)?)\s*\$?\s*(\d+(?:\.\d+)?)",
            r"\$\s*(\d+(?:\.\d+)?)",
            r"(?:under|below|within)\s*(\d+(?:\.\d+)?)\s*k\b",
        ]

        for i, pattern in enumerate(patterns):
            m = re.search(pattern, q)
            if not m:
                continue
            value = float(m.group(1))
            if i == 2:
                value *= 1000
            return value

        return None

preference_chain = PreferenceChain()
