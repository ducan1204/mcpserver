from typing import Optional
from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel

from ollama.ollama_services import get_embedding
from .qdrant_services import (
    create_collection, 
    delete_collection, 
    get_collection, 
    check_collection_exists, 
    insert_vectors, 
    insert_vector, 
    get_vector,
    search
)
from qdrant_client.http.models import PointStruct
import fitz
import uuid
from chunking.get_chunks import (
    getMixedChunks,
    getVariableSizeSubChunks,
    getVariableSizeChunks,
    getFixedSizeChunks,
    getFamilyChunks
)
router = APIRouter(prefix="/api/v1/qdrant")

class CreateCollectionRequest(BaseModel):
    collection_name: str
    vector_size: int
    distance: str = "Dot"

class RetrievalSetting(BaseModel):
    top_k: Optional[int] = 3
    score_threshold: Optional[float] = 0.5

class SearchRequest(BaseModel):
    knowledge_id: str
    query: str
    retrieval_setting: Optional[RetrievalSetting] = None


@router.get("/collections")
async def getCollection(name: str):
    collection = get_collection(name)
    return collection

@router.post("/collections")
async def createCollection(request: CreateCollectionRequest):
    """
    Create a new collection in Qdrant.
    """
    create_collection(request.collection_name, request.vector_size, request.distance)

@router.delete("/collections/{collection_name}")
async def deleteCollection(collection_name: str):
    """
    Delete a collection from Qdrant.
    """
    delete_collection(collection_name)

@router.post("/collections/{collection_name}/check")
async def checkCollectionExists(collection_name: str):
    """
    Check if a collection exists in Qdrant.
    """
    exists = check_collection_exists(collection_name)
    return exists

@router.post("/collections/{collection_name}/vector/")
async def insertVerctor(collection_name: str, embedding: list):
    """
    Insert a single vector into the specified collection.
    """
               # Adjust as needed to get vector data
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=embedding,
        payload={}
    )
    result = insert_vector(collection_name, point)
    return result

@router.post("/text")
async def insertText(collection_name: str, text: str):
    """
    Insert a text vector into the specified collection.
    """
    # Here you would typically convert the text to a vector
    # For demonstration, we will use a dummy vector
    embedding = get_embedding(text)
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=embedding,
        payload={"text": text}
    )
    result = insert_vector(collection_name, point)
    return result

@router.post("/file")
async def insertFile(collection_name: str,file: UploadFile = File(...)):
    """
    Insert a file vector into the specified collection.
    """
    content = await file.read()
    fileExtension = file.filename.split(".")[-1]
    text = ""

    if fileExtension == "pdf":
        pdf = fitz.open(stream=content, filetype=fileExtension)
    
        for page_num, page in enumerate(pdf):
            text += page.get_text()
    elif fileExtension == "txt":
        text = content.decode("utf-8")
    else:
        raise ValueError("Unsupported file format")

    # chunks = await getFixedSizeChunks(text, chunkSize=1000)
    # chunks = await getVariableSizeChunks(text, marker="^^^")
    chunks = await getFamilyChunks(text, marker="^^^", submarker="|||", minLength=200)
    # chunks = await getMixedChunks(text, marker="^^^", submarker="---", minLength=200)
    # Here you would typically convert the file content to a vector
    # For demonstration, we will use a dummy vector
    for chunk in chunks:
        embedding = await get_embedding(chunk)
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload={"collection": collection_name, "file_name": file.filename, "file_content": chunk}
        )
        result = insert_vector(collection_name, point)
    return chunks

@router.post("/collections/{collection_name}/search/")
async def searchCollection(collection_name: str, text: str, limit: int = 3):
    """
    Search for vectors in the specified collection.
    """
    points = await get_embedding(text)
    result = search(collection_name, points, limit=limit, with_payload=True)
    return result

@router.post("/retrieval")
async def searchCollection(request: SearchRequest):
    """
    Search for vectors in the specified collection.
    """
    print(request)
    points = await get_embedding(request.query)
    result = search(request.knowledge_id, points, limit=request.retrieval_setting.top_k, with_payload=True)

    transformedResults = []
    for item in result:
        payload = item.payload or {}
        transformedResults.append({
            "metadata": {
            #     "path": f"s3://dify/{payload.get('file_name', 'unknown')}",
            #     "description": "dify knowledge document"  # or customize as needed
            },
            "score": item.score,
            "title": payload.get("file_name", ""),
            "content": payload.get("file_content", "")
        })
    return {"records": transformedResults}