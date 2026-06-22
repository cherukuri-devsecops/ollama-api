import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Any
import os
import json

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

app = FastAPI(title="Ollama API Gateway", version="1.0.0")


class GenerateRequest(BaseModel):
    model: str
    prompt: str
    stream: bool = False
    options: dict[str, Any] | None = None


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    stream: bool = False
    options: dict[str, Any] | None = None


class EmbeddingRequest(BaseModel):
    model: str
    prompt: str


class PullRequest(BaseModel):
    model: str
    stream: bool = False


@app.get("/health")
async def health():
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            resp.raise_for_status()
            return {"status": "ok", "ollama": "reachable"}
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Ollama unreachable: {e}")


@app.get("/models")
async def list_models():
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))


@app.post("/generate")
async def generate(req: GenerateRequest):
    payload = {"model": req.model, "prompt": req.prompt, "stream": req.stream}
    if req.options:
        payload["options"] = req.options

    if req.stream:
        return StreamingResponse(
            _stream_ollama("/api/generate", payload),
            media_type="text/event-stream",
        )

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/generate", json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))


@app.post("/chat")
async def chat(req: ChatRequest):
    payload = {
        "model": req.model,
        "messages": [m.model_dump() for m in req.messages],
        "stream": req.stream,
    }
    if req.options:
        payload["options"] = req.options

    if req.stream:
        return StreamingResponse(
            _stream_ollama("/api/chat", payload),
            media_type="text/event-stream",
        )

    async with httpx.AsyncClient(timeout=120) as client:
        try:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))


@app.post("/embeddings")
async def embeddings(req: EmbeddingRequest):
    async with httpx.AsyncClient(timeout=60) as client:
        try:
            resp = await client.post(
                f"{OLLAMA_BASE_URL}/api/embeddings",
                json={"model": req.model, "prompt": req.prompt},
            )
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))


@app.post("/pull")
async def pull_model(req: PullRequest):
    payload = {"name": req.model, "stream": req.stream}

    if req.stream:
        return StreamingResponse(
            _stream_ollama("/api/pull", payload),
            media_type="text/event-stream",
        )

    async with httpx.AsyncClient(timeout=600) as client:
        try:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/pull", json=payload)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))


@app.get("/version")
async def version():
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            resp = await client.get(f"{OLLAMA_BASE_URL}/api/version")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))


@app.get("/models/{model_name}")
async def model_info(model_name: str):
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.post(f"{OLLAMA_BASE_URL}/api/show", json={"name": model_name})
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))


@app.delete("/models/{model_name}")
async def delete_model(model_name: str):
    async with httpx.AsyncClient(timeout=30) as client:
        try:
            resp = await client.request(
                "DELETE", f"{OLLAMA_BASE_URL}/api/delete", json={"name": model_name}
            )
            resp.raise_for_status()
            return {"deleted": model_name}
        except httpx.HTTPStatusError as e:
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
        except Exception as e:
            raise HTTPException(status_code=503, detail=str(e))


async def _stream_ollama(path: str, payload: dict):
    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream("POST", f"{OLLAMA_BASE_URL}{path}", json=payload) as resp:
            resp.raise_for_status()
            async for chunk in resp.aiter_text():
                yield f"data: {chunk}\n\n"
