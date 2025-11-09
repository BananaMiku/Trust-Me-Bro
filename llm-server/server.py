import json
import os
import subprocess
import sys

CHEAP_MODEL = 'b'

import requests
from fastapi import BackgroundTasks, FastAPI, Request, Response
from pydantic import BaseModel

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import MODELS, MODES, InternalRequest, get_port_no, send_internal_request

app = FastAPI()
app.state.response_mode = "normal"
app.state.port = get_port_no("load")


@app.get("/submit_prompt")
def submit(data: InternalRequest, request: Request):
    print("load server received:", data)

    response_mode = request.app.state.response_mode
    response = handle_prompt_request(data, response_mode)
    print(response.content)
    return response.json()


@app.get("/mode")
def get_mode(request: Request):
    return {"mode": request.app.state.response_mode}


class ModeRequest(BaseModel):
    mode: str


@app.post("/switch_mode")
def submit(mode: ModeRequest, request: Request): 
    request.app.state.response_mode = mode.mode 
    return { "status": "success", }

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
            internal_request.model = CHEAP_MODEL 
    return send_internal_request(internal_request)
