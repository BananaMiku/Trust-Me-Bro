import asyncio
import os
import random
import shlex
import subprocess

import pandas as pd
import structlog
from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel


class UUID(BaseModel):
    userID: str
    model: str


class SMIData(BaseModel):
    gpuUtilization: float
    vramUsage: float
    powerDraw: float
    uuid: UUID


tmb = FastAPI()
log = structlog.get_logger()
# TODO with c, move the reservoir/buffer size to a global config file
reservoir_size = 10

pendingRequests: dict[str, dict] = {}


async def cache_and_average(userID, model, gpuUtilization, vramUsage, powerDraw):
    # data normalized from rust side
    session = pendingRequests[userID]
    async with session["Lock"]:
        session["Cache"].append(
            {
                "Model": model,
                "gpuUtilization": gpuUtilization,
                "vramUsage": vramUsage,
                "powerDraw": powerDraw,
            }
        )

        cache = session["Cache"]
        n = len(cache)
    return {
        "gpuAvg": sum(num["gpuUtilization"] for num in cache) / n,
        "vramAvg": sum(num["vramUsage"] for num in cache) / n,
        "powerAvg": sum(num["powerDraw"] for num in cache) / n,
    }


# could def be optimized lol
def reservoir_sampling(model, gpuUtilization, vramUsage, powerDraw):
    filePath = f"{model}_storage.csv"

    # one data as row
    row = pd.DataFrame(
        [
            {
                "gpuUtilization": gpuUtilization,
                "vramUsage": vramUsage,
                "powerDraw": powerDraw,
            }
        ]
    )

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
    userID = uuid.userID
    log.info(f"{userID} Reached /clientRequest")
    if userID not in pendingRequests:
        pendingRequests[userID] = {
            "Event": asyncio.Event(),
            "Cache": [],
            "Verification": None,
        }

    session = pendingRequests[userID]
    try:
        await asyncio.wait_for(session["Event"].wait(), timeout=6)
        return {"Verified": session["Verification"]}
    except asyncio.TimeoutError:
        err = "Verification Process Timed Out"
        log.error(err)
        raise HTTPException(status_code=408, detail=err)
    except Exception:
        err = "Client Request Error"
        log.error(err)
        raise HTTPException(status_code=500, detail=err)
    finally:
        pendingRequests.pop(userID, None)


# incoming data from LLM server
@tmb.post("/metrics")
async def metrics(smiData: SMIData):
    userID = smiData.uuid.userID
    log.info(f"{userID} Reached /metrics")
    if userID not in pendingRequests:
        pendingRequests[userID] = {
            "Event": asyncio.Event(),
            "Cache": [],
            "Verification": None,
        }
        # raise HTTPException(status_code=400, detail=f"No Active Session For {userID}")

    session = pendingRequests[userID]
    session["Cache"].append(
        {
            "model": smiData.uuid.model,
            "gpuUtilization": smiData.gpuUtilization,
            "vramUsage": smiData.vramUsage,
            "powerDraw": smiData.powerDraw,
        }
    )

    return {"message": "Receiving Data"}


class FINISH(BaseModel):
    userID: str


# continuously ingest data at /metric endpoint until /finished is hit
@tmb.post("/finished")
async def finished(req: FINISH, request: Request):
    userID = req.userID
    log.info(f"{userID} Reached /finished")
    if userID not in pendingRequests:
        raise HTTPException(status_code=400, detail="No Active Session")

    session = pendingRequests[userID]
    cache = session["Cache"]

    if not cache:
        raise HTTPException(status_code=400, detail="No Data Received")

    # find average
    n = len(cache)
    model = cache[0]["model"]
    gpuAvg = sum(items["gpuUtilization"] for items in cache) / n
    vramAvg = sum(items["vramUsage"] for items in cache) / n
    powerAvg = sum(items["powerDraw"] for items in cache) / n

    # reservoir sampling
    reservoir_sampling(model, gpuAvg, vramAvg, powerAvg)

    # compile c file
    baseDir = os.path.dirname(os.path.abspath(__file__))
    cFile = os.path.join(baseDir, "stats_verify.c")
    cExecutable = os.path.join(baseDir, "stats_verify")
    storageFile = os.path.join(baseDir, f"{model}_storage.csv")
    try:
        log.info("Compiling C File...")
        # build dependencies
        deps = [
            os.path.join(baseDir, "utils.c"),
            os.path.join(baseDir, "gpu-utilization", "utils.c"),
            os.path.join(baseDir, "powerdraw", "utils.c"),
            os.path.join(baseDir, "vram", "utils.c"),
        ]
        # get GSL flags
        try:
            pkg_flags = subprocess.check_output(
                ["pkg-config", "--cflags", "--libs", "gsl"], text=True
            ).strip()
            flags = shlex.split(pkg_flags)
        except Exception as e:
            log.error(f"Install GSL on Your Machine: {e}")
            return e
        # build gcc command
        cmd = ["gcc", cFile, *deps, "-o", cExecutable, *flags]
        subprocess.run(cmd, check=True)
        # subprocess.run(["gcc", cFile, "-o", cExecutable], check=True)
    except subprocess.CalledProcessError as e:
        log.error(f"Error Compiling C File: {e}")
        return e
    # build input arguments
    arguments = [str(storageFile), str(gpuAvg), str(vramAvg), str(powerAvg)]

    try:
        result = subprocess.run(
            [cExecutable] + arguments,
            capture_output=True,
            text=True,
            check=True,
            cwd=baseDir,
        )
        verification = result.returncode
        # sums true + false, <= 1 means majority true
        if verification <= 1:
            session["Verification"] = True
        else:
            session["Verification"] = False

        log.info(f"Setting Events for: {session['Event']}")
        session["Event"].set()  # release clientRequest waiter
        return {"Verification Result": session["Verification"]}
    except subprocess.CalledProcessError as e:
        log.error(f"STDOUT: {e.stdout}")
        log.error(f"STDERR: {e.stderr}")
        return e
    except Exception as e:
        log.error(f"Error Executing C Binary: {e}")
        return e
