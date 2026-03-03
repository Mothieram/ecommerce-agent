from transformers import pipeline, BitsAndBytesConfig
import torch

# 1. Configure 4-bit quantization settings
quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16, # High precision for computation
    bnb_4bit_quant_type="nf4",             # Recommended for normal-distributed weights
    bnb_4bit_use_double_quant=True         # Saves even more memory
)

# 2. Initialize the pipeline with the quantization config
pipe = pipeline(
    "text-generation", 
    model="google/gemma-3-1b-it", 
    device_map="auto",                     # Automatically handles device placement
    model_kwargs={"quantization_config": quantization_config}
)

# 3. Define messages using the standard format
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Write a poem on Hugging Face, the company"},
]

# 4. Generate output
# Note: Gemma 3 uses a specific chat template handled by the pipeline
output = pipe(messages, max_new_tokens=100)
print(output[0]['generated_text'][-1]['content'])