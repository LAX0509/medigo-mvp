from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from backend.user_router import router as user_router
from backend.medical_router import router as medical_router

# 👇 Mueve docs y openapi a rutas que no choque con "/"
app = FastAPI(
    title="App Médica API",
    version="1.0.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API primero
app.include_router(user_router, prefix="/api/v1")
app.include_router(medical_router, prefix="/api/v1")

# Frontend después (sirviendo SPA en "/")
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")

