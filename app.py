from fastapi import FastAPI, Request, UploadFile, File
from pydantic import BaseModel
from sklearn import base
import uvicorn
from client import main as run_agent
from conversation_graph import main as ask
import fitz
from save_documents_to_vector import save_content
from modules.app.app_module import get_app_module
from ollama.ollama_services import get_embedding
from qdrant.qdrant_controllers import router as qdrant_router

app = FastAPI()

# Define the input model
class QuestionRequest(BaseModel):
    question: str
    document_id: str

class EmbedRequest(BaseModel):
    text: str

@app.post("/ask")
async def ask_agent(request: QuestionRequest):
    try:
        print("Received question:", request.question)
        # result = await run_agent(request.question, request.document_id)
        result = await ask(request.question)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
@app.post("/upload")
async def upload(file: UploadFile = File(...)):
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

    await save_content(text, file.filename, fileExtension, file.size)
    
    return fileExtension

@app.post("/embed")
async def embed_document(request: EmbedRequest):
    try:
        text = request.text
        
        
        # Call the embedding function here
        # For example, you can call a function to get embeddings
        embeddings = await get_embedding(text)
        # print(embeddings)
        
        return {"status": "success", "embedding": embeddings}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
app.include_router(get_app_module())
app.include_router(qdrant_router)