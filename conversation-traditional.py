import asyncio
from typing import Annotated, TypedDict
from langchain.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from langgraph.graph.message import add_messages
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
    SystemMessagePromptTemplate,
)
load_dotenv()

class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", api_key=GOOGLE_API_KEY, max_tokens=4096)

memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
prompt = ChatPromptTemplate.from_messages([
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessagePromptTemplate.from_template("{input}"),
    SystemMessagePromptTemplate.from_template("You are a helpful assistant."),
])
conversation_chain = ConversationChain(
    llm=llm,
    prompt=prompt,
    memory=memory,
    verbose=False
)



async def chatbot(message: str):
    response = conversation_chain.invoke({"input": message})
    print("LLM Response:", response.get('response'))
    print("memory", memory)
    return {"messages": [response]}

async def main():
    try:
        while True:
            try:
                user_input = input("User: ")
                if user_input.lower() in ["quit", "exit", "q"]:
                    print("Goodbye!")
                    break
                await chatbot(user_input)
            except Exception as e:
                print("Error:", e)
                break
    except Exception as e:
        print(e)

        
def create_contextual_query(user_input):
    history = memory.load_memory_variables({})['history']
    context_str = "\n".join(history + [user_input])
    return context_str

if __name__ == "__main__":
    asyncio.run(main())
# print(conversation_chain.invoke({"input": "Hello, how are you?"}))

# print(conversation_chain.invoke({"input": "can you help me with my homework?"}))
