import asyncio
import sys
from dotenv import load_dotenv
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from pydantic import BaseModel
from typing import List, Optional
from pydantic import HttpUrl
from fastapi import FastAPI
from tools import get_tools
from langchain_core.messages import HumanMessage

# Load environment variables from .env file
load_dotenv()
app = FastAPI()
# Get API keys from environment variables
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=GOOGLE_API_KEY, max_tokens=4096)

python_path = sys.executable  # Get Python executable path

class IndustrialPark(BaseModel):
    name: str
    price_per_m2: Optional[str] = None
    area: Optional[str] = None
    description: Optional[str] = None
    address: Optional[str] = None
    occupancy_rate: Optional[str] = None
    lease_area_options: Optional[str] = None
    legal_status: Optional[str] = None
    lease_term: Optional[str] = None
    advantages: Optional[str] = None
    additional_info: Optional[str] = None
    detail_url: Optional[HttpUrl] = None
    image: Optional[HttpUrl] = None
    reason: Optional[str] = None

class ResponseFormat(BaseModel):
    text: str
    # objects: List[IndustrialPark]

async def main(question: str, document_id: str):
    # Create the AI agent
    systemPrompt = """Try to use tools to answer user question"""

    agent = create_react_agent(
        model, 
        get_tools(), 
        debug=False, 
        prompt=systemPrompt,
        response_format=ResponseFormat
    )

    request = {
        "messages": [
            HumanMessage(content=f"{question}. document_id={document_id}")
        ]
    }
    results = await agent.ainvoke(debug=True, input=request)
    parsed_data = parse_ai_messages(results)
    return parsed_data
            
async def main_loop():
    while True:
        question = input("Question> ")
        if question.lower() == "exit":
            return
        await main(question, "0f129423-eff9-486f-8ee9-979be55b1974")

def parse_ai_messages(data):
    structured_response = dict(data).get('structured_response', [])
    # print(f"Structured Response: {structured_response}")
    return structured_response

# if __name__ == "__main__":
#     asyncio.run(main_loop())
    