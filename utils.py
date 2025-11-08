from pydantic import BaseModel
import requests
server_url = "http://127.0.0.1:8000/submit/"

MODELS = ["gpt5", "gpt4", "gpt3"]

class PromptRequest(BaseModel):
    uuid: str
    prompt: str
    model: str

class InternalRequest(BaseModel):
    original: PromptRequest
    uuid: str
    prompt: str

def send_prompt_request(prompt_request):
    to_send = prompt_request_to_json(prompt_request)
    response = requests.post(server_url, json=to_send)
    print(response.status_code)
    print(response.json())
    return response.json()

def prompt_request_to_json(prompt_request):
    ret = {
        "uuid": prompt_request.uuid,
        "prompt": prompt_request.prompt,
        "model": prompt_request.model
    }
    return ret

def internal_request_to_json(internal_request):
    ret = {
        "original": prompt_request_to_json(internal_request.original),
        "prompt": internal_request.prompt,
        "model": internal_request.model
    }
    return ret

def send_internal_request(internal_request, server_url):
    to_send = internal_request_to_json(internal_request) 
    response = requests.post(server_url, json=data)
    return response.json()
