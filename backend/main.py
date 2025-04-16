import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from loguru import logger
import uvicorn

from app.api import router as api_router
from services.db import init_db

# Load environment variables
load_dotenv()

# Configure logger
logger.add("logs/api.log", rotation="500 MB", level="INFO")

app = FastAPI(
    title="DSB But Better API",
    description="API für die Verarbeitung von DSBmobile-Stundenplänen",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix="/api")

@app.on_event("startup")
async def startup_event():
    """Initialize database connection and other services on startup"""
    logger.info("Starting up DSB But Better API")
    await init_db()

@app.on_event("shutdown")
async def shutdown_event():
    """Close connections and perform cleanup on shutdown"""
    logger.info("Shutting down DSB But Better API")

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "online", "message": "DSB But Better API is running"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
