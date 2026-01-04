from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from app.routers import recommend


app = FastAPI(
    title="NextTrack API",
    description="A stateless music recommendation API",
    version="0.1.0",
)

app.include_router(recommend.router, prefix="/api/v1")


@app.get("/")
def root():
    return {"message": "NextTrack API is running"}


@app.get("/api/v1/health")
def health_check():
    return {"status": "healthy"}
