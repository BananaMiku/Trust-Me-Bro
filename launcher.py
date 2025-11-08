#!/bin/python
import argparse
import os

import uvicorn

from utils import get_port_no

WRAPPER_MTP = "a,3222;b,3223"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", type=str, required=True)
    args = parser.parse_args()
    match args.server:
        case "load":
            uvicorn.run(
                "llm-server.server:app",
                host="0.0.0.0",
                port=get_port_no("load"),
                reload=True,
            )

        case "tmb":
            uvicorn.run(
                "tmb-server.tmb:tmb",
                host="0.0.0.0",
                port=get_port_no("tmb"),
                reload=True,
            )

        case "wrapper":
            os.execv(
                "./wrapper/target/debug/wrapper",
                [
                    "./wrapper/targets/debug/wrapper",
                    WRAPPER_MTP,
                    str(get_port_no("wrapper")),
                ],
            )
        case "model":  # if the binary doesnt exist go to llama.cpp, run cmake -B build -DGGML_CUDA=ON -DBUILD_SHARED_LIBS=OFF, cmake --build build --config Release -j 8 --target llama-server
            executable = "llama.cpp/build/bin/llama-server"
            os.execv(
                executable,
                [
                    executable,
                    "-hf",
                    "ggml-org/gemma-3-1b-it-GGUF",  # model type
                    "--port",
                    str(get_port_no("model")),
                ],
            )
        case _:
            print("not a valid program name")
