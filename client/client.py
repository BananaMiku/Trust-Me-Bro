import requests
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import MODELS, PromptRequest, InternalRequest, send_prompt_request, set_mode, get_mode, get_port_no


class PromptRequest:
    def __init__(self, uuid, prompt, model):
        self.uuid = uuid
        self.prompt = prompt
        self.model = model


if __name__ == "__main__":
    load_url = "http://127.0.0.1:{}".format(get_port_no("load"))
    print(load_url)
    send_prompt_request(PromptRequest(uuid="id 1", prompt="10", model="gpt5"))
    set_mode("skimp", load_url)
    print(get_mode(load_url))
    send_prompt_request(PromptRequest(uuid="id 1", prompt="10", model="gpt5"))
