import subprocess
import asyncio
import structlog
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class UUID(BaseModel):
    userID: str
    model: str

class SMIData(BaseModel):
    gpuUtilization: float
    vramUsage: float
    powerDraw : float
    uuid: UUID

tmb = FastAPI()
log = structlog.get_logger()

pendingRequests: dict[str: (asyncio.Event, bool)] = {}

@tmb.post("/clientRequest")
async def clientRequest(uuid: UUID):
    # create event, await, die if timeout
    # new request, create new event
    id = uuid.userID
    if id not in pendingRequests:
        event = asyncio.Event()
        pendingRequests[id] = (event, None)
    try:
        await asyncio.wait_for(event.wait(), timeout=10)
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

@tmb.post("/incomingData")
async def incomingData(smiData: SMIData):
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
    arguments = [
        str(smiData.gpuUtilization),
        str(smiData.vramUsage),
        str(smiData.powerDraw),
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