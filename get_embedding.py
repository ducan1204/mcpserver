from transformers import AutoTokenizer, AutoModel
from sentence_transformers import SentenceTransformer
import torch
import asyncio 
import unicodedata
from pgvector import embed_text
import json

nomic = "nomic-ai/nomic-embed-text-v1"
phobert = "vinai/phobert-base"
allMiniLm = 'sentence-transformers/all-MiniLM-L6-v2'
multilingual = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2' #384
vietnamsbert = 'keepitreal/vietnamese-sbert' #768

async def get_embedding(text: str):
    model = vietnamsbert
    embedder = SentenceTransformer(model)
    embedding = embedder.encode(text, normalize_embeddings=True)

    return embedding.tolist()

async def encode_and_decode(text: str):
    model = multilingual
    print(f"Dùng model {model}")
    text = unicodedata.normalize("NFC", text)
    tokenizer = AutoTokenizer.from_pretrained(model)
    encoded = tokenizer.encode(text, add_special_tokens=False)

    decoded = tokenizer.decode(encoded, skip_special_tokens=True)


# asyncio.run(get_embedding("Tôi yêu việt nam"))
# asyncio.run((embed_text("Tôi yêu việt nam")))
# asyncio.run(encode_and_decode("Tôi yêu việt nam"))