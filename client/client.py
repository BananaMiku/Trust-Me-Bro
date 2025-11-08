import requests
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils import MODELS, PromptRequest, InternalRequest, send_prompt_request

server_url = "http://127.0.0.1:8000/submit/"

if __name__ == "__main__":
    send_prompt_request(PromptRequest(uuid="id 1", prompt="10", model="gpt5"))
