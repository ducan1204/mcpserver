from math import e
import requests

async def get_embedding(text, model="nomic-embed-text"):
    """
    Get embedding from Ollama API at localhost:31803/api/embed.

    Args:
        text (str): The input text to embed.
        model (str): The model name to use (optional).

    Returns:
        list: The embedding vector.
    """
    url = "http://10.66.68.17:31803/api/embed"
    payload = {
        "model": model,
        "input": text
    }
    response = requests.post(url, json=payload)
    embedding = response.json().get("embeddings")[0]
    # print(embedding)
    
    return embedding