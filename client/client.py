#!/bin/python
import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from utils import (
    MODELS,
    InternalRequest,
    get_mode,
    get_port_no,
    send_prompt_request,
    set_mode,
)


class PromptRequest:
    def __init__(self, uuid, prompt, model):
        self.uuid = uuid
        self.prompt = prompt
        self.model = model


if __name__ == "__main__":
    load_url = "http://127.0.0.1:{}".format(get_port_no("load"))
    messages = []
    while True:
        userInput = input()
        messages.append({"role": "user", "content": userInput})
        to_send = InternalRequest(
            original=f'{{"messages": {json.dumps(messages)}}}',
            uuid="id 1",
            model="a",
        )
        print("client sending request")
        print("client received request", send_prompt_request(to_send))
