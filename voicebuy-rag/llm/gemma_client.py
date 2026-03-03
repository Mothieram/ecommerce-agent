from langchain_huggingface import HuggingFacePipeline
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    pipeline,
    BitsAndBytesConfig,
)
import torch
from core.config import settings


class GemmaClient:
    def __init__(self):
        self.llm = None

    def load(self):
        print("Loading Gemma (4-bit quantized)...")

        token = settings.HF_TOKEN.strip() if settings.HF_TOKEN else None

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_quant_type="nf4",
        )

        tokenizer_kwargs = {}
        if token:
            tokenizer_kwargs["token"] = token

        model_kwargs = {
            "quantization_config": bnb_config,
            "device_map": "auto",
        }
        if token:
            model_kwargs["token"] = token

        tokenizer = AutoTokenizer.from_pretrained(
            settings.GEMMA_MODEL_ID,
            **tokenizer_kwargs,
        )

        model = AutoModelForCausalLM.from_pretrained(
            settings.GEMMA_MODEL_ID,
            **model_kwargs,
        )

        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=256,
            temperature=0.7,
            do_sample=True,
            return_full_text=False,
        )

        self.llm = HuggingFacePipeline(pipeline=pipe)
        print("Gemma loaded successfully")

    def get_llm(self):
        if not self.llm:
            self.load()
        return self.llm


gemma_client = GemmaClient()
