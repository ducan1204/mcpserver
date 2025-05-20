import enum
from re import I
import nltk
# nltk.download('punkt_tab')
from nltk.tokenize import sent_tokenize
from read_pdf_file import extract_file_content
import asyncio
from transformers import AutoTokenizer
from typing import List
import uuid
from get_embedding import get_embedding
from save_documents_to_vector import insert_parents, Document, insert_childs, DocumentChildChunk
import json


multilingual = 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2' #384
tokenizer = AutoTokenizer.from_pretrained(multilingual)

class ParentChunk():
    def __init__(self, id, content):
        self.id = id
        self.content = content

class ChildChunk():
    def __init__(self, id, content, parent_id, embedding = None):
        self.id = id
        self.content = content
        self.parent_id = parent_id
        self.embedding = embedding

async def chunk_parents(text):
    chunks = 0
    start = 0

    while start < len(t):
        parent_chunks = text.split('\n\n')
    return parent_chunks

async def chunk_by_delimiter(text, delimiter='\n\n') -> List[ParentChunk]:
    return [ParentChunk(id=uuid.uuid4(), content=chunk) for i, chunk in enumerate(text.split(delimiter))]

async def split_or_merge_chunk(parentChunks: List[ParentChunk]) -> List[ParentChunk]:
    max_tokens = 400
    min_tokens = 50
    final_chunks: List[ParentChunk] = []
    current_chunk = ""

    for parentChunk in parentChunks:
        if parentChunk.content.strip() == "":
            continue
        tokens = tokenizer.encode(parentChunk.content, add_special_tokens=False)
        num_tokens = len(tokens)
        if num_tokens < min_tokens:
            # Gộp vào chunk trước đó nếu có
            if final_chunks:
                final_chunks[-1] = parentChunk
            else:
                current_chunk += " " + parentChunk.content  # trường hợp đầu tiên
        elif num_tokens <= max_tokens:
            parentChunk.content = tokenizer.decode(tokens)
            final_chunks.append(parentChunk)
        else:
            # Nếu chunk lớn hơn max_tokens thì chia nhỏ
            split_subchunks: List[ParentChunk] = []
            token_chunks = [tokens[i:i+max_tokens] for i in range(0, len(tokens), max_tokens)]
            current_subchunk = ""
            for token_subchunk in token_chunks:
                decoded = tokenizer.decode(token_subchunk)
                current_subchunk += " " + decoded

                if (len(token_subchunk) >= min_tokens):
                    split_subchunks.append(ParentChunk(id = uuid.uuid4(), content=current_subchunk))
                    current_subchunk = ""
            if (current_subchunk):
                split_subchunks.append(ParentChunk(id=uuid.uuid4(), content=current_subchunk))
            final_chunks.extend(split_subchunks)

    return final_chunks

async def splitted_child_chunks(parentChunks: List[ParentChunk]) -> List[ChildChunk]:
    max_tokens = 100
    min_tokens = 10
    final_chunks: List[ChildChunk] = []
    
    for parentChunk in parentChunks:
        parentContent = tokenizer.encode(parentChunk.content, add_special_tokens=False)
        num_tokens = len(parentContent)

        if num_tokens <= max_tokens:
            # Gộp vào chunk trước đó nếu có
            final_chunks.append(ChildChunk(id=uuid.uuid4(), content=parentChunk.content, parent_id=parentChunk.id))
        else:
            childTokens = [parentContent[i:i+max_tokens] for i in range(0, len(parentContent), max_tokens)]
            
            tmpChild = ""
            for childToken in childTokens:
                if (len(childToken) > min_tokens):
                    final_chunks.append(ChildChunk(id=uuid.uuid4(), content=tokenizer.decode(childToken), parent_id=parentChunk.id))
                else:
                    tmpChild += " " + tokenizer.decode(childToken)
            if tmpChild:
                final_chunks.append(ChildChunk(id=uuid.uuid4(), content=tmpChild, parent_id=parentChunk.id))
    return final_chunks


async def run():
    path = "/home/suga/Desktop/Work/faq/santa/Script_CSKH_training_AI.pdf"
    text = extract_file_content(path, False)

    parent_chunks = await chunk_by_delimiter(text, "\n\n")

    splitted_parent_chunks = await split_or_merge_chunk(parent_chunks)

    listDocuments = [Document(id=chunk.id, content=chunk.content) for chunk in splitted_parent_chunks]

    split_child_chunks = await splitted_child_chunks(splitted_parent_chunks)
    listChildDocuments = []
    for i, child in enumerate(split_child_chunks):
        child.embedding = await get_embedding(child.content)
        print(f"Embedding {i}")
        listChildDocuments.append(DocumentChildChunk(id=child.id, content=child.content, document_chunk_id=child.parent_id, embedding=json.dumps(child.embedding)))
    await insert_parents(listDocuments)
    await insert_childs(listChildDocuments)

        

        

asyncio.run(run())