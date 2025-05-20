
import requests


async def embed_text(text):
    url = "http://10.66.68.17:31802/api/embed"
    embedModel = "nomic-embed-text"
    data = {
        "input": text,
        "model": embedModel
    }
    headers = {
        "Content-Type": "application/json"
    }
    response = requests.post(url, json=data, headers=headers)
    
    embeddings = response.json()["embeddings"]
    print(embeddings[0])

    return embeddings[0]
