import asyncio
from re import split
from typing import List
import uuid
import asyncpg
from pgvector import embed_text
import json
from read_pdf_file import extract_file_content, chunk_text
from typing_extensions import TypedDict
from chunk_content import chunk_by_delimiter, split_or_merge_chunk, splitted_child_chunks
from get_embedding import get_embedding


conn = None

class Document(TypedDict):
    id: str
    name: str
    file_extension: str
    size: int

class DocumentChunk(TypedDict):
    id: str
    content: str
    position: int
    page_number: int
    topic: str
    metadata: dict
    document_id: str

class DocumentChildChunk(TypedDict):
    id: str
    content: str
    embedding: str
    document_id: str
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

async def insert_parents(parentChunks: List[DocumentChunk]):
    await establish_connection()
    # print((parentChunks[0]))
    records = [
        (parent['id'], parent['content'], parent['document_id'])
        for parent in parentChunks
    ]
    await conn.executemany('''
        INSERT INTO document_chunks (id, content, document_id) 
        VALUES ($1, $2, $3)''', 
        records
    )

async def insert_childs(childChunks: List[DocumentChildChunk]):
    await establish_connection()
    print((childChunks[0]))
    records = [
        (parent['id'], parent['content'], parent['embedding'], parent['document_chunk_id'], parent['document_id'])
        for parent in childChunks
    ]
    await conn.executemany('''
        INSERT INTO document_child_chunks (id, content, embedding, document_chunk_id, document_id) 
        VALUES ($1, $2, $3, $4, $5)''', 
        records
    )

async def insert_document_chunk(documentChunk: DocumentChunk):
    await conn.execute('''
        INSERT INTO documents (content, embedding, topic, section) 
        VALUES ($1, $2, $3, $4)''', 
        documentChunk['content'], 
        json.dumps(documentChunk['embedding']), 
        documentChunk['topic'], 
        documentChunk['section']
    )

async def insert_document_chunks(documentChunks: List[DocumentChunk]):
    records = [
        (chunk['content'], json.dumps(chunk['embedding']), chunk['topic'], chunk['section'])
        for chunk in documentChunks
    ]
    await conn.executemany('''
        INSERT INTO documents (content, embedding, topic, section) 
        VALUES ($1, $2, $3, $4)''', 
        records
    )

async def insert_document(document: Document):
    await conn.execute('''
        INSERT INTO documents (id, name, file_extension, size) 
        VALUES ($1, $2, $3, $4)''',
        document['id'],
        document['name'], 
        document['file_extension'], 
        document['size']
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

    await insert_document_chunks(documents)

async def save_content(content, file_name, file_extension, file_size):
    await establish_connection()
    # parent_chunks, child_chunks, metadata = chunk_text(content)
    # print(parent_chunks)

    # text = extract_file_content(path, False)

    parent_chunks = await chunk_by_delimiter(content, "\n\n")

    splitted_parent_chunks = await split_or_merge_chunk(parent_chunks)

    document = Document(
        id=uuid.uuid4(),
        name=file_name,
        file_extension=file_extension,
        size=file_size
    )
    await insert_document(document)
    # print(document)
    listDocumentChunks = [DocumentChunk(id=chunk.id, content=chunk.content, document_id=document['id']) for chunk in splitted_parent_chunks]

    split_child_chunks = await splitted_child_chunks(splitted_parent_chunks)

    listChildDocuments = []
    for i, child in enumerate(split_child_chunks):
        child.embedding = await get_embedding(child.content)
        print(f"Embedding {i}")
        listChildDocuments.append(DocumentChildChunk(id=child.id, content=child.content, document_chunk_id=child.parent_id, document_id=document['id'], embedding=json.dumps(child.embedding)))
    await insert_parents(listDocumentChunks)
    await insert_childs(listChildDocuments)

    # documents = []
    # for chunk in child_chunks:
    #     embedding = await embed_text(chunk)
    #     document = {
    #         'content': chunk,
    #         'embedding': embedding,
    #         'topic': '',
    #         'section': ''
    #     }
    #     documents.append(document)

    # await insert_document_chunks(documents)

# async def run():
#     path = "/home/suga/Desktop/Work/faq/santa/Script_CSKH_training_AI.pdf"
#     await save_documents(path)

# asyncio.run(run())
    