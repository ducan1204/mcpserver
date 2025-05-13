from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn
from client import main as run_agent

app = FastAPI()

# Define the input model
class QuestionRequest(BaseModel):
    question: str

@app.post("/ask")
async def ask_agent(request: QuestionRequest):
    try:
        print("Received question:", request.question)
        result = await run_agent(request.question)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)