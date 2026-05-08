from fastapi import APIRouter

router = APIRouter()


@router.get("/osint/search")
async def osint_search(q: str):

    return {
        "query": q,
        "status": "running",
        "results": [
            f"Resultado OSINT para: {q}"
        ]
    }


@router.get("/")
async def root():

    return {
        "status": "online",
        "core": "Hoppy Black-Core",
        "mode": "agentic"
    }