from utils import get_port_no 
import argparse
import os
import uvicorn

WRAPPER_MTP = "a,3222;b,3223"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", type=str, required=True)
    args = parser.parse_args()
    match args.server:
        case "load":
            uvicorn.run("llm-server.server:app", host="0.0.0.0", port=get_port_no("load"), reload=True)

        case "tmb":
            uvicorn.run("tmb-server.tmb:tmb", host="0.0.0.0", port=get_port_no("tmb"), reload=True)

        case "wrapper":
            os.execv("./wrapper/wrapper", ["./wrapper/wrapper", WRAPPER_MTP, str(get_port_no("wrapper"))])
        case _:
            print("not a valid program name")

