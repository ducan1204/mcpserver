import asyncio
from typing import List
import asyncpg
from pgvector import embed_text
import json
from read_pdf_file import extract_file_content, chunk_text
from typing_extensions import TypedDict
from get_embedding import get_embedding
from save_documents_to_vector import Document, DocumentChildChunk

conn = None

async def search(text: str, document_id: str):
    conn =  await asyncpg.connect(user='postgres', password='123456', database='main', host='10.66.68.17', port=31803)

    # embedding = await embed_text(text)
    embedding = await get_embedding(text)

    
    nearest: List[DocumentChildChunk] = await conn.fetch('''
        Select *, embedding <=> $2 as distance from document_child_chunks where document_id = $1 order by embedding <=> $2 limit 5
    ''', document_id, json.dumps(embedding))

    # docs = [{k: v for k, v in doc.items() if k != 'embedding'} for doc in nearest]
    distinct_parents = {doc['document_chunk_id'] for doc in nearest}
    for chunk_id in distinct_parents:
        print(chunk_id)

    related_docs: List[Document] = await conn.fetch('''
        SELECT * from document_chunks where id = ANY($1) and document_id = $2
    ''', distinct_parents, document_id)
    # print([doc['content'] for doc in related_docs])
    # return related_docs
    return [doc['content'] for doc in related_docs]

# print(asyncio.run(search("santaeshop là gì", "0f129423-eff9-486f-8ee9-979be55b1974")))