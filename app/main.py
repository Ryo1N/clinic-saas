# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.db import init_db
from app.routers import public, doctor

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="Clinic SaaS MVP", lifespan=lifespan)
app.include_router(public.router, prefix="/api/public", tags=["public"])
app.include_router(doctor.router, prefix="/api/doctor", tags=["doctor"])

@app.get("/")
def root():
    return {"message": "Clinic SaaS backend is running!"}


app.mount("/web", StaticFiles(directory="app/web", html=True), name="web")