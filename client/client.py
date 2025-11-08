import requests
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import MODELS, InternalRequest, send_prompt_request, set_mode, get_mode, get_port_no


class PromptRequest:
    def __init__(self, uuid, prompt, model):
        self.uuid = uuid
        self.prompt = prompt
        self.model = model


if __name__ == "__main__":
    load_url = "http://127.0.0.1:{}".format(get_port_no("load"))
    print(load_url)
    to_send = InternalRequest(original='{"messages": [{"role": "user", "content": "hello"}]}', uuid="id 1", model="gpt5")
    send_prompt_request(to_send)
