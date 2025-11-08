from fastapi import FastAPI, BackgroundTasks, Request
from pydantic import BaseModel
import requests, subprocess, json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import MODELS, MODES, PromptRequest, InternalRequest, get_port_no, send_internal_request, prompt_request_to_json
app = FastAPI()
app.state.response_mode = "normal"
app.state.port = get_port_no("load")

@app.post("/submit_prompt")
def submit(data: PromptRequest, background_tasks: BackgroundTasks, request: Request):
    #asserts the request is valid
    if data.model not in MODELS:
        raise HTTPException(status_code=500, detail={})

    response_mode = request.app.state.response_mode
    background_tasks.add_task(handle_prompt_request, data, response_mode)

    
    return {
        "status": "accepted", 
        "uuid": data.uuid
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

def handle_prompt_request(prompt_request: PromptRequest, response_mode: str):
    internal_request = InternalRequest(original=prompt_request_to_json(prompt_request), uuid=prompt_request.uuid, model=prompt_request.model)
    match response_mode:
        case "skimp":
            internal_request.model = "b"
    send_internal_request(internal_request)

def handle_prompt_request(request):
    print("uuid: {}, model: {}, prompt: {}".format(request.uuid, request.model, request.prompt))

    result = f"Output for prompt '{request.prompt}'"

    try:
        metrics_json = subprocess.check_output(["./metrics_analyzer"], text=True)
        try:
            metrics_data = json.loads(metrics_json)
        except json.JSONDecodeError:
            print("[WARN] metrics_analyzer did not return valid JSON, using raw text.")
            metrics_data = [{"raw_output": metrics_json.strip()}]
    except Exception as e:
        print(f"[ERROR] Could not run metrics_analyzer: {e}")
        metrics_data = []

    #Send output + metrics back to your Trust-Me-Bro backend
    if isinstance(metrics_data, list):
        metrics_list = [{"type": "model_output", "value": result}] + metrics_data
    else:
        metrics_list = [{"type": "model_output", "value": result}, metrics_data]

    payload = {
        "query_uuid": str(request.uuid),
        "metrics": metrics_list
    } 

    #send to tmb server
    try:
        tmb_url = "http://127.0.0.1:8001/metrics/"
        response = requests.post(tmb_url, json=payload)
        print("[INFO] Sent payload to TMB:", response.status_code)
    except Exception as e:
        print(f"[ERROR] Failed to send to TMB server: {e}")
