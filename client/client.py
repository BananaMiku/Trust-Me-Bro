import requests

server_url = "http://127.0.0.1:8000/submit/"

class PromptRequest:
    uuid: int
    prompt: str
    model: str

def send_prompt_request(PromptRequest):
    to_send = {
        "uuid": PromptRequest.uuid,
        "prompt": PromptRequest.prompt,
        "model": PromptRequest.prompt
    }
    response = requests.post(server_url, json=data)
    print(response.status_code)
    print(response.json())
    return response.json()
