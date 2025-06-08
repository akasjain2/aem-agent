from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_community.llms import HuggingFacePipeline

MODEL_NAME = "NousResearch/Nous-Hermes-2-Mistral-7B-DPO"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME, use_fast=False)  # 👈 Force slow tokenizer

model = AutoModelForCausalLM.from_pretrained(
    MODEL_NAME,
    torch_dtype="auto",
    device_map="auto"
)

pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=512,
    temperature=0.3,
    do_sample=True,
)

llm = HuggingFacePipeline(pipeline=pipe)
