from fastapi import FastAPI
from pydantic import BaseModel
from .agent_graph import build_graph

app = FastAPI()
graph = build_graph()

class Request(BaseModel):
    jira_id: str

@app.post("/analyze")
def analyze(request: Request):
    print('Received request:', request)
    result = graph.invoke({"jira_id": request.jira_id})
    return result
