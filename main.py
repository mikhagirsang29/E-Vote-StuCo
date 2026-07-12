import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend

import database
from database import SessionLocal, User, ElectionState
from routes.admin import admin_router
from routes.client import client_router

# 1. Initialize Cache on Startup and seed admin
@asynccontextmanager
async def lifespan(app: FastAPI):
    FastAPICache.init(InMemoryBackend(), prefix="election")
    db = SessionLocal()
    if not db.query(ElectionState).filter(ElectionState.id == 1).first():
        db.add(ElectionState(id=1, status="SETUP"))
    if not db.query(User).first():
        db.add(User(student_id="admin", password="password", role="admin"))
    db.commit()
    db.close()
    yield

app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/script", StaticFiles(directory="script"), name="script")

# Ensure upload folder exists
os.makedirs("static/uploads", exist_ok=True)

app.include_router(client_router)
app.include_router(admin_router)
