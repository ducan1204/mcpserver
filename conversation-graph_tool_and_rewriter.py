from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.tools import Tool
import os
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import Annotated, List
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from pydantic import BaseModel
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langchain.chat_models import init_chat_model
import asyncio
from ollama.ollama_services import get_embedding as get_ollama_embedding
from qdrant.qdrant_services import search as qdrant_search
import json
load_dotenv()

GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

class State(TypedDict):
    # Messages have the type "list". The `add_messages` function
    # in the annotation defines how this state key should be updated
    # (in this case, it appends messages to the list, rather than overwriting them)
    messages: Annotated[list, add_messages]

class AgentState:
    messages: list

class SearchSantaInfoArgs(BaseModel):
    messages: str

memory = MemorySaver()
async def search_santa_info(messages: str, limit: int = 5) -> dict:
    """Tìm kiếm thông tin về hệ sinh thái Santa (Santa ecosystem). Sử dụng tool này khi người dùng hỏi về Santa hoặc các thông tin liên quan."""
    
    # print("messages:", messages)
    points = await get_ollama_embedding(messages)
    result = qdrant_search("documents", points, limit=limit, with_payload=True)
    # print("result:", result)
    # for document in result:
    #     print(document.payload.get('file_content', ""))
    context = " ".join(document.payload.get('file_content', " ") for document in result)
    print(context)
    return context
santaTool = Tool(
    name="search_santa_info",
    description="Tìm kiếm thông tin về hệ sinh thái Santa (Santa ecosystem). Sử dụng tool này khi người dùng hỏi về Santa hoặc các thông tin liên quan.",
    func=search_santa_info,
    args_schema=SearchSantaInfoArgs,
)
tools = [santaTool]
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash", 
    api_key=GOOGLE_API_KEY, 
    max_tokens=4096, 
)
llm_with_tools = llm.bind_tools(tools)

async def chatbot(state: State):
    response: AIMessage = await llm_with_tools.ainvoke(state["messages"])
    return {"messages": [response]}

async def print_dry_answer(messages: List[any]):
    for message in messages:
        print(message.content)

async def stream_graph_updates(user_input: str):
    async for event in graph.astream({"messages": [{"role": "user", "content": user_input}]}, config=config):
        print(event)
        for value in event.values():
            for msg in value["messages"]:
                print("Bot:", msg.content)
async def summary_graph_updates(history_messages: List[any]):
    summary_instruction = "Summary all information you can collect from conversation in short, less than 50 words."
    rewrite_messages = history_messages + [HumanMessage(content=summary_instruction)]
    try:
        async for event in rewrite_graph.astream({"messages": rewrite_messages}, config=rewriteconfig):
            for value in event.values():
                for msg in value["messages"]:
                    print("Rewriter:", msg.content)
    except Exception as e:
        print(e)

async def extract_memory(thread_id: str):
    # print("Memory============")
    config_for_state = {"configurable": {"thread_id": thread_id}}
    checkpoint_tuple = await memory.aget_tuple(config_for_state)
    extracted_messages = []
    if checkpoint_tuple:
        for key, value in checkpoint_tuple.checkpoint.items():
            if key == "channel_values":
                extracted_messages = value.get('messages')[-6:]
        # await print_dry_answer(extracted_messages)
        return extracted_messages
    else:
        print(f"No history found for thread '{thread_id}'.")
        return []

config = {"configurable": {"thread_id": "1"}}
rewriteconfig = {"configurable": {"thread_id": "2"}}

class BasicToolNode:
    "A node that runs the tools requested in the last AI Message"
    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}

    def __call__(self, inputs: dict):
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []
        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(
                tool_call["args"]
            )
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}
def route_tools(
    state: State,
):
    """
    Use in the conditional_edge to route to the ToolNode if the last message
    has tool calls. Otherwise, route to the end.
    """
    print("stateeeeeeeeeeeeeeeeeee", state)
    if isinstance(state, list):
        ai_message = state[-1]
    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END

tool_node = BasicToolNode(tools=tools)
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
graph_builder.add_node("tools", tool_node)
graph_builder.add_conditional_edges(
    "chatbot",
    route_tools,
    # The following dictionary lets you tell the graph to interpret the condition's outputs as a specific node
    # It defaults to the identity function, but if you
    # want to use a node named something else apart from "tools",
    # You can update the value of the dictionary to something else
    # e.g., "tools": "my_tools"
    {"tools": "tools", END: END},
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile(checkpointer=memory)

rewrite_graph_builder = StateGraph(State)
rewrite_graph_builder.add_node("chatbot", chatbot)
rewrite_graph_builder.add_edge(START, "chatbot")
rewrite_graph = rewrite_graph_builder.compile(checkpointer=memory)

async def main():
    current_thread_id = "1"
    while True:
        try:
            user_input = input("User: ")
            if user_input.lower() in ["quit", "exit", "q"]:
                print("Goodbye!")
                break
            if user_input.lower() in ["mem"]:
                await extract_memory(current_thread_id)
            else:
                await stream_graph_updates(user_input)
                # history = await extract_memory(current_thread_id)
                # await summary_graph_updates(history)
            
        except Exception as e:
            print("Error:", e)
            break

if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run((search_santa_info("santa là gì", 1)))


# asyncio.run(santaTool.invoke({"messages":"santa là gì"}))