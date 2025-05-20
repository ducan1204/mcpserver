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

async def search(text: str):
    conn =  await asyncpg.connect(user='postgres', password='123456', database='main', host='10.66.68.17', port=31803)

    # embedding = await embed_text(text)
    embedding = await get_embedding(text)

    
    nearest: List[DocumentChildChunk] = await conn.fetch('''
        Select *, embedding <=> $1 as distance from document_child_chunks order by embedding <=> $1 limit 5
    ''', json.dumps(embedding))

    # docs = [{k: v for k, v in doc.items() if k != 'embedding'} for doc in nearest]
    distinct_parents = {doc['document_chunk_id'] for doc in nearest}
    for chunk_id in distinct_parents:
        print(chunk_id)

    related_docs: List[Document] = await conn.fetch('''
        SELECT * from document_chunks where id = ANY($1)
    ''', distinct_parents)
    # print([doc['content'] for doc in related_docs])
    # return related_docs
    return [doc['content'] for doc in related_docs]

# print(asyncio.run(search("santaeshop là gì")))