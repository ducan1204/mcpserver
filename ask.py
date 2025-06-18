
#!/home/suga/Desktop/Work/learn/local-mcp/py-mcp-server/venv/bin/python
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, SystemMessage
load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=GOOGLE_API_KEY, max_tokens=4096)
async def ask(question, target_language='vi'):
    messages = [
        SystemMessage("Answer user question"),
        HumanMessage(question),
    ]
    response = model.invoke(messages)
    return response.content

if __name__ == '__main__':
    while True:
        question = input("Input your question: ")
        if question == 'exit':
            break
        result = asyncio.run(ask(question))
        print(f"================== Result ==================")
        print(result)
        print(f"\n\n")
