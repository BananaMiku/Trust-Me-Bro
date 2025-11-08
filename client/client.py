import requests
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import MODELS, PromptRequest, InternalRequest, send_prompt_request, set_mode, get_mode

server_url = "http://127.0.0.1:8000"

if __name__ == "__main__":
    send_prompt_request(PromptRequest(uuid="id 1", prompt="10", model="gpt5"))
    set_mode("skimp", server_url)
    print(get_mode(server_url))
    send_prompt_request(PromptRequest(uuid="id 1", prompt="10", model="gpt5"))
