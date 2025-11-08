import subprocess
import asyncio
import structlog
import os
import random
import pandas as pd
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class UUID(BaseModel):
    userID: str
    model: str

class SMIData(BaseModel): # TODO double check this
    gpuUtilization: float
    vramUsage: float
    powerDraw : float
    uuid: UUID

tmb = FastAPI()
log = structlog.get_logger()
# TODO with c, move the reservoir/buffer size to a global config file
reservoir_size = 10

pendingRequests: dict[str: (asyncio.Event, bool)] = {}

# could def be optimized lol
def reservoir_sampling(model, gpuUtilization, vramUsage, powerDraw):
    filePath = f"{model}_storage.csv"

    # one data as row
    # TODO trim to maybe 3 decimal places
    # TODO update dataframe only after the c calculation
    row = pd.DataFrame([{
        "gpuUtilization": gpuUtilization,
        "vramUsage": vramUsage,
        "powerDraw": powerDraw,
    }])

    # read storage file, create one if none exists
    if os.path.exists(filePath) and os.path.getsize(filePath) > 0:
        try:
            df = pd.read_csv(filePath, index_col=False)
        except pd.errors.EmptyDataError:
            # exists exists but is blank
            df = pd.DataFrame(columns=row.columns)
    else:
        df = pd.DataFrame(columns=row.columns)


    # reservoir sampling
    if len(df) >= reservoir_size:
        # replace a random row
        idx = random.randrange(len(df))
        df.iloc[idx] = row.iloc[0]
    else:
        df = pd.concat([df, row], ignore_index=True)

    df.to_csv(filePath, index=False)

@tmb.post("/clientRequest")
async def clientRequest(uuid: UUID):
    # create event, await, die if timeout
    # new request, create new event
    id = uuid.userID
    if id not in pendingRequests:
        event = asyncio.Event()
        pendingRequests[id] = (event, None)
    try:
        await asyncio.wait_for(event.wait(), timeout=1)
        _, verified = pendingRequests[id]
        return verified
    except asyncio.TimeoutError:
        err = "Verification Process Timed Out"
        log.error(err)
        raise HTTPException(status_code=408, detail=err)
    except Exception:
        err = "Client Request Error"
        log.error(err)
        raise HTTPException(status_code=500, detail=err)
    finally:
        pendingRequests.pop(id)

# incoming data from LLM server
@tmb.post("/metrics")
async def metrics(smiData: SMIData):
    id = smiData.uuid.userID
    if id not in pendingRequests:
        # this technically should not happen?
        return "IDK man what?"
    
    event, _ = pendingRequests[id]
    # stats_verify is the compiled c code for stats verification
    # compile c file
    baseDir = os.path.dirname(os.path.abspath(__file__))
    cFile = os.path.join(baseDir, "stats_verify.c")
    cExecutable = os.path.join(baseDir, "stats_verify")
    try:
        log.info("Compiling C File...")
        subprocess.run(["gcc", cFile, "-o", cExecutable], check=True)
        
    except subprocess.CalledProcessError as e:
        log.error(f"Error Compiling C File: {e}")
        return e
    
    # build arguments for c file
    # convert to str for subprocess.run
    reservoir_sampling(smiData.uuid.model, smiData.gpuUtilization, smiData.vramUsage, smiData.powerDraw)
    # TODO beta bound[0,1] for gpu utilization, normalize to this range if not already
    # clip any external values because why would it ever go outside of 0-1 after normalizing
    # cannot be 0 or 1, if 0, add small noise, if 1, subtract a small noise
    arguments = [
        str(smiData.uuid.model + "_storage.csv"),
        str(smiData.gpuUtilization),
        str(smiData.vramUsage),
        str(smiData.powerDraw)
    ]
    
    # execute c file
    try:
        result = subprocess.run([cExecutable] + arguments, 
                                capture_output=True,
                                text=True, 
                                check=True)
        verification = result.stdout
        # update
        event, _ = pendingRequests[id]
        pendingRequests[id] = event, verification
        event.set()
        return verification
    except subprocess.CalledProcessError as e:
        log.error(f"C Standard Error: {e.stderr}")
        return e
    except Exception as e:
        log.error(f"Error Executing C Binary: {e}")
        return e