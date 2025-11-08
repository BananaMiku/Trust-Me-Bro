from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel

app = FastAPI()

MODELS = ["gpt5", "gpt4", "gpt3"]

class PromptRequest(BaseModel):
    uuid: int
    prompt: str
    model: str

@app.post("/submit/")
def submit(data: PromptRequest, background_tasks: BackgroundTasks):
    #asserts the request is valid
    if data.model not in MODELS:
        return {
            "status": "error"
        }

    background_tasks.add_task(handle_prompt_request, data)
    
    return {
        "status": "success",
    }

def handle_prompt_request(request):
    print("uuid: {}, model: {}, prompt: {}".format(request.uuid, request.model, request.prompt))
