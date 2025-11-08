import pytest
import asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from tmb import tmb

# run pytest -v
# gpt generated awesomeness
client = TestClient(tmb)

def test_client_request_timeout():
    """If no incomingData arrives, the request should eventually time out."""
    params = {"userID": "test_user", "model": "GPT-5"}
    response = client.post("/clientRequest", json=params)
    assert response.status_code == 408

def test_incoming_data_without_waiter():
    """If /metrics is called with no matching waiter, return error message."""
    params = {
        "gpuUtilization": 75.5,
        "vramUsage": 60.1,
        "powerDraw": 200.0,
        "uuid": {
            "userID": "ghost_user",
            "model": "GPT-5",
        },
    }
    response = client.post("/metrics", json=params)
    assert "IDK" in response.text

@pytest.mark.asyncio
async def test_client_request_success():
    userData = {"userID": "test_user", "model": "GPT-5"}
    smiData = {
        "gpuUtilization": 80.5,
        "vramUsage": 70.1,
        "powerDraw": 250.0,
        "uuid": userData,
    }
    transport = ASGITransport(app=tmb)

    async def send_client_request():
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            return await ac.post("/clientRequest", json=userData)

    client_task = asyncio.create_task(send_client_request())
    await asyncio.sleep(0.5)

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res_incoming = await ac.post("/metrics", json=smiData)
        assert res_incoming.status_code == 200

    res_client = await client_task
    assert res_client.status_code == 200