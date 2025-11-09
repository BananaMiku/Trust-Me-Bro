from fastapi import FastAPI, BackgroundTasks, Request
from pydantic import BaseModel
import requests, subprocess, json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import MODELS, MODES, InternalRequest, get_port_no, send_internal_request 
app = FastAPI()
app.state.response_mode = "normal"
app.state.port = get_port_no("load")

@app.get("/submit_prompt")
def submit(data: InternalRequest, request: Request):
    print("load server received:", data)

    response_mode = request.app.state.response_mode
    response = handle_prompt_request(data, response_mode)

    print("load server received: ", response)
    return response.json()

@app.get("/mode")
def get_mode(request: Request):
    return {"mode": request.app.state.response_mode}

class ModeRequest(BaseModel):
    mode: str

# @app.post("/switch_mode")
# def submit(mode: ModeRequest, request: Request):
#     #asserts the request is valid
#     if mode.mode not in MODES:
#         raise HTTPException(status_code=500, detail={})

#     request.app.state.response_mode = mode.mode 

#     return {
#         "status": "success",
#     }

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

def handle_prompt_request(internal_request: InternalRequest, response_mode: str):
    match response_mode:
        case "skimp":
            internal_request.model = "b"
    return send_internal_request(internal_request)

