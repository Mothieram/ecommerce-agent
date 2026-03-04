import re

def clean_llm_output(text: str) -> str:
    """Strip Gemma turn markers and extra whitespace from LLM output."""
    text = re.sub(r'<start_of_turn>|<end_of_turn>', '', text)
    text = re.sub(r'\bmodel\b', '', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_json_string(text: str) -> str:
    """Extract first JSON object found in LLM output."""
    match = re.search(r'\{{.*?\}}', text, re.DOTALL)
    return match.group() if match else '{}'
