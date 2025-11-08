from pydantic import BaseModel
import re
import os
import json
import requests
server_url = "http://127.0.0.1:8000"

MODELS = ["gpt5", "gpt4", "gpt3"]
MODES = ["normal", "skimp"]
PROMPT_REQUEST_PATH = "/submit_prompt"
INTERNAL_REQUEST_PATH = "/internal"
GET_MODE_PATH = "/mode" 
SET_MODE_PATH = "/switch_mode" 

base_dir = os.path.dirname(os.path.abspath(__file__))
PORT_FILE = os.path.join(base_dir, "port_map.txt")

def get_port_no(process_name):
    with open(PORT_FILE, 'r') as file:
        for line in file.readlines():
            matches = re.findall(r'([a-zA-z]+): ([0-9]+)', line)
            if matches[0][0] == process_name:
                return int(matches[0][1])
    return None 

load_url = "http://127.0.0.1:{}".format(get_port_no("load"))
class PromptRequest(BaseModel):
    uuid: str
    prompt: str
    model: str

class InternalRequest(BaseModel):
    original: PromptRequest
    uuid: str
    model: str

def send_prompt_request(prompt_request):
    to_send = json.dumps(prompt_request)
    response = requests.post("{}{}".format(load_url, PROMPT_REQUEST_PATH), json=to_send)
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
        "original": json.dumps(prompt_request_to_json(internal_request.original)),
        "uuid": internal_request.uuid,
        "model": internal_request.model
    }
    return ret

def send_internal_request(internal_request):
    to_send = internal_request_to_json(internal_request) 
    wrapper_url = "http://127.0.0.1:{}/".format(3822)
    print(wrapper_url)

    headers = {"Content-Type": "application/json"}
    response = requests.post(wrapper_url, data=json.dumps(to_send), headers=headers)
    print("sent, status code:", response.status_code)
    print("response:", response.text)

def get_mode(server_url):
    response = requests.get("{}{}".format(server_url, GET_MODE_PATH), json={})
    return response.json()

def set_mode(mode, server_url):
    data = {"mode": mode}
    response = requests.post("{}{}".format(server_url, SET_MODE_PATH), json=data)
    return response.json()
