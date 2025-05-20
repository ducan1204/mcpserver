import asyncio
from typing import List
import asyncpg
from pgvector import embed_text
import json
from read_pdf_file import extract_file_content, chunk_text
from typing_extensions import TypedDict


conn = None

class Document(TypedDict):
    id: str
    content: str
    position: int
    page_number: int
    topic: str
    metadata: dict

class DocumentChildChunk(TypedDict):
    id: str
    content: str
    embedding: str
    document_chunk_id: str
    position: int
    topic: str
    section: str
    metadata: dict






async def fetch():
    rows = await conn.fetch('''
        Select * from document_child_chunks
    ''')
    return rows

async def insert_parents(parentChunks: List[Document]):
    await establish_connection()
    print((parentChunks[0]))
    records = [
        (parent['id'], parent['content'])
        for parent in parentChunks
    ]
    await conn.executemany('''
        INSERT INTO document_chunks (id, content) 
        VALUES ($1, $2)''', 
        records
    )

async def insert_childs(childChunks: List[DocumentChildChunk]):
    await establish_connection()
    print((childChunks[0]))
    records = [
        (parent['id'], parent['content'], parent['embedding'], parent['document_chunk_id'])
        for parent in childChunks
    ]
    await conn.executemany('''
        INSERT INTO document_child_chunks (id, content, embedding, document_chunk_id) 
        VALUES ($1, $2, $3, $4)''', 
        records
    )

async def insert_document(document: Document):
    await conn.execute('''
        INSERT INTO documents (content, embedding, topic, section) 
        VALUES ($1, $2, $3, $4)''', 
        document['content'], 
        json.dumps(document['embedding']), 
        document['topic'], 
        document['section']
    )

async def insert_documents(documents: List[Document]):
    records = [
        (doc['content'], json.dumps(doc['embedding']), doc['topic'], doc['section'])
        for doc in documents
    ]
    await conn.executemany('''
        INSERT INTO documents (content, embedding, topic, section) 
        VALUES ($1, $2, $3, $4)''', 
        records
    )

async def establish_connection():
    global conn 
    if conn is None:
        conn = await asyncpg.connect(user='postgres', password='123456', database='main', host='10.66.68.17', port=31803)

async def save_documents(path):
    await establish_connection()
    file_content = extract_file_content(path)
    parent_chunks, child_chunks, metadata = chunk_text(file_content)
    # print(parent_chunks)

    documents = []
    for chunk in child_chunks:
        embedding = await embed_text(chunk)
        document = {
            'content': chunk,
            'embedding': embedding,
            'topic': '',
            'section': ''
        }
        documents.append(document)

    await insert_documents(documents)

# async def run():
#     path = "/home/suga/Desktop/Work/faq/santa/Script_CSKH_training_AI.pdf"
#     await save_documents(path)

# asyncio.run(run())
    