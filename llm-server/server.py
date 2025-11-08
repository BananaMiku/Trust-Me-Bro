from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import requests
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import MODELS, PromptRequest, InternalRequest

app = FastAPI()

<<<<<<< HEAD
MODELS = ["gpt5", "gpt4", "gpt3"]

class PromptRequest(BaseModel):
    uuid: int
    prompt: str
    model: str

class MetricsPayload(BaseModel):
    query_uuid: str
    metrics: list

=======
>>>>>>> 2521504 (cleaned client server stuff)
@app.post("/submit/")
def submit(data: PromptRequest, background_tasks: BackgroundTasks):
    #asserts the request is valid
    if data.model not in MODELS:
        return {
            "status": "error"
        }

    background_tasks.add_task(handle_prompt_request, data)
    
    return {
        "status": "success",
    }

@app.post("/metrics/")
def receive_metrics(payload: MetricsPayload):
    print("Received metrics for UUID:", payload.query_uuid)
    print(payload.metrics)
    return {"status": "success"}

def handle_prompt_request(request):
    print("uuid: {}, model: {}, prompt: {}".format(request.uuid, request.model, request.prompt))

