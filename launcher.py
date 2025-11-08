from utils import get_port_no 
import argparse
import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", type=str, required=True)
    args = parser.parse_args()
    match args.server:
        case "load":
            uvicorn.run("llm-server.server:app", host="0.0.0.0", port=get_port_no("load"), reload=True)
        case _:
            print("not a valid program name")

