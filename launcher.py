#!/bin/python
import argparse
import subprocess
import threading

import uvicorn

from utils import client, get_port_no

WRAPPER_MTP = "a,3222;b,3223"


def launch_load():
    """Launch the load server in a blocking call (to be run in a thread)."""
    uvicorn.run(
        "llm-server.server:app",
        host="0.0.0.0",
        port=get_port_no("load"),
        reload=False,
    )


def launch_tmb():
    """Launch the tmb server in a blocking call (to be run in a thread)."""
    uvicorn.run(
        "tmb-server.tmb:tmb",
        host="0.0.0.0",
        port=get_port_no("tmb"),
        reload=False,
    )


def launch_wrapper():
    """Launch the wrapper executable as a subprocess."""
    subprocess.Popen(
        [
            "./wrapper/target/debug/wrapper",
            WRAPPER_MTP,
            str(get_port_no("wrapper")),
        ]
    )


def launch_model():
    """Launch the model server as a subprocess."""
    subprocess.Popen(
        [
            "./llama.cpp/build/bin/llama-server",
            "-hf",
            "ggml-org/gemma-3-1b-it-GGUF",
            "--port",
            str(get_port_no("model")),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    subprocess.Popen(
        [
            "./llama.cpp/build/bin/llama-server",
            "-hf",
            "ggml-org/gemma-3-270m-it-GGUF",
            "--port",
            str(get_port_no("model") + 1),
        ],
        stdout=subprocess.DEVNULL,
    )


def launch_all():
    load_thread = threading.Thread(target=launch_load, daemon=True)
    tmb_thread = threading.Thread(target=launch_tmb, daemon=True)

    load_thread.start()
    print("launched load")

    tmb_thread.start()
    print("launched tmb")

    launch_wrapper()
    print("launched wrapper")

    launch_model()
    print("launched model")

    from time import sleep

    sleep(2)
    print("----------------")
    client()

    load_thread.join()
    tmb_thread.join()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", type=str, required=False, default="all")
    args = parser.parse_args()

    match args.server:
        case "load":
            launch_load()
        case "tmb":
            launch_tmb()
        case "wrapper":
            launch_wrapper()
        case "model":
            launch_model()
        case _:
            launch_all()
