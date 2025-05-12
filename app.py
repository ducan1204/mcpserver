from fastapi import FastAPI, Request
from pydantic import BaseModel
from client import main as run_agent

app = FastAPI()

# Define the input model
class QuestionRequest(BaseModel):
    question: str

@app.post("/ask")
async def ask_agent(request: QuestionRequest):
    try:
        result = await run_agent(request.question)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}