from fastapi import FastAPI, Request
from pydantic import BaseModel
import uvicorn
from client import main as run_agent

app = FastAPI()
def bootstrap():
    #do something
    print('a')

bootstrap()