#!/bin/python
import json
import os
import sys
import threading

from textual import on
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.validation import Function, Number, ValidationResult, Validator
from textual.widgets import Input, Label, Pretty, Select

from utils import (
    MODELS,
    InternalRequest,
    get_mode,
    get_port_no,
    send_prompt_request,
    set_mode,
)

class Prompt(Label):
    def __init__(self, prompt: str, model: str) -> None:
        super().__init__(prompt)
        self.model = model

    def on_mount(self) -> None:
        self.border_title = self.model


class Response(Label):
    def __init__(self, response: str, model: str, verified: bool) -> None:
        super().__init__(response)
        self.model = model
        self.verified = verified

    def on_mount(self) -> None:
        self.border_title = self.model
        self.border_subtitle = f"verified: {self.verified}"
        if self.verified:
            self.add_class(f"-valid")


class InputApp(App):
    def __init__(self) -> None:
        super().__init__()
        self.load_url = "http://127.0.0.1:{}/".format(get_port_no("load"))
        self.messages = []

    CSS = """
    Input.-valid {
        border: tall $success 60%;
    }
    Input.-valid:focus {
        border: tall $success;
    }
    Input {
        margin: 1 1;
    }
    Label {
        margin: 1 2;
    }
    Pretty {
        margin: 1 2;
    }
    Select {
        margin: 1 2;
    }
    Response {
            align: left top;
            text_align: left;
            width: 100%;
            padding: 0 1;
            margin: 1 20 1 1;
            border: heavy $surface 100%;
            border-title-color: $primary;
            border-subtitle-color: $warning;
    }

    Response.-valid {
            border-subtitle-color: $success;
    }

    Prompt {
            align: right top;
            text_align: right;
            width: 100%;
            padding: 0 1;
            margin: 1 1 1 20;
            border: heavy $surface 100%;
            border-title-align: right;
            border-title-color: $primary;
    }

    VerticalScroll {
        scrollbar-size: 1 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Label("Trust Me Bro")
        yield Select.from_values(["a", "b"], allow_blank=False)
        yield VerticalScroll(
            id="messages",
        )
        yield Input(
            placeholder="ask anything",
        )

    @on(Input.Submitted)
    def on_submit(self, event: Input.Submitted) -> None:
        self.app
        # gets the model
        select_widget = self.query_one(Select)
        model = select_widget.value

        #updates scroll with our msg
        scroll = self.query_one("#messages", VerticalScroll)
        scroll.mount(Prompt(event.input.value, model))
        scroll.scroll_end(animate=False)
        event.input.value = ""
        self.refresh()
        self.run_worker(self.get_res(event.input.value, model))


    async def get_res(self, prompt, model):
        container = self.query_one('#messages', VerticalScroll)
        self.messages.append({"role": "user", "content": prompt})
        to_send = InternalRequest(
                original=f'{{"messages": {json.dumps(self.messages)}}}',
                uuid="id 1",
                model=model,
                )
        res = send_prompt_request(to_send)
        #self.messages.append(res)
        #updates the response 
        container.mount(Response(str(res['choices'][0]['message']['content']), model, False))
        container.scroll_end(animate=False)

<<<<<<< HEAD
=======
        #get the ver
        ver = requests.post(
            f"http://localhost:{get_port_no('tmb')}/clientRequest",
            json={"userID": "id 1", "model": "gpt5"},
        ).content

>>>>>>> 8854b92 (still me, writting stuff)
if __name__ == "__main__":
    app = InputApp()
    app.run()
