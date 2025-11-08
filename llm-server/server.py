from fastapi import FastAPI, BackgroundTasks, Request
from pydantic import BaseModel
import requests
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import MODELS, MODES, PromptRequest, InternalRequest, get_port_no

app = FastAPI()
app.state.response_mode = "normal"
app.state.port = get_port_no("load")

@app.post("/submit_prompt")
def submit(data: PromptRequest, background_tasks: BackgroundTasks, request: Request):
    #asserts the request is valid
    if data.model not in MODELS:
        raise HTTPException(status_code=500, detail={})

    background_tasks.add_task(handle_prompt_request, data, request)
    
    return {
        "status": "success",
    }

@app.get("/mode")
def get_mode(request: Request):
    return {"mode": request.app.state.response_mode}

class ModeRequest(BaseModel):
    mode: str

@app.post("/switch_mode")
def submit(mode: ModeRequest, request: Request):
    #asserts the request is valid
    if mode.mode not in MODES:
        raise HTTPException(status_code=500, detail={})

    request.app.state.response_mode = mode.mode 

    return {
        "status": "success",
    }

class MetricsPayload(BaseModel):
    query_uuid: str
    metrics: list

@app.post("/metrics/")
def receive_metrics(payload: MetricsPayload):
    print("Received metrics for UUID:", payload.query_uuid)
    print(payload.metrics)
    return {"status": "success"}
class PromptRequest(BaseModel):
    uuid: str
    prompt: str
    model: str

class InternalRequest(BaseModel):
    original: PromptRequest
    uuid: str
    model: str

def handle_prompt_request(prompt_request, request: Request):
    internal_request = InternalRequest(original=prompt_request, uuid=prompt_request.uuid, model=prompt_request.model)
    match request.app.state.response_mode:
        case "skimp":
            send_internal_request(internal_request, server_url)
        case _:
            send_internal_request(internal_request, server_url)

