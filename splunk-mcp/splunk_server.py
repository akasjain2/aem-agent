from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class SplunkQuery(BaseModel):
    package_name: str
    timestamp: str

@app.post("/splunk/query")
def query_logs(data: SplunkQuery):
    return {
        "log_text": f"Simulated log for package {data.package_name} at {data.timestamp}\nError: java.lang.RuntimeException"
    }
