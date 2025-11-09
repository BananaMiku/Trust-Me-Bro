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
import importlib.util
from pathlib import Path

app = FastAPI()
app.state.response_mode = "normal"
app.state.port = get_port_no("load")
app.state.load_balancer = None


@app.on_event("startup")
def startup_event():
    # start the load balancer with default number of workers and wrapper port
    wrapper_port = get_port_no("wrapper") or 3222
    # dynamically load the load_balancer module from file to avoid package-name issues
    lb_path = Path(__file__).parent / "load_balancer.py"
    spec = importlib.util.spec_from_file_location("llm_load_balancer", str(lb_path))
    lb_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(lb_mod)
    lb = lb_mod.LoadBalancer(num_workers=None, wrapper_port=wrapper_port)
    app.state.load_balancer = lb


@app.post("/submit_prompt")
def submit(data: InternalRequest, request: Request):
    # enqueue the internal request to the worker pool for processing
    print("load server received:", data)
    response_mode = request.app.state.response_mode
    # apply mode modifications
    if response_mode == "skimp":
        data.model = "b"

    # prepare a plain dict task to send to wrapper from worker
    task = {
        "original": {
            "uuid": data.original.uuid,
            "prompt": data.original.prompt,
            "model": data.original.model,
        },
        "uuid": data.uuid,
        "model": data.model,
    }

    lb = request.app.state.load_balancer
    if lb is None:
        return {"status": "error", "reason": "load balancer not initialized"}

    wid = lb.enqueue(task)
    return {"status": "accepted", "worker": wid, "uuid": data.uuid}


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
