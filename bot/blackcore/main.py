from fastapi import FastAPI
from blackcore.routes.osint_routes import router as osint_router

app = FastAPI()

app.include_router(osint_router)