from fastapi import FastAPI
from app.api.repository import router as repository_router

app = FastAPI()

app.include_router(
    repository_router,
    prefix="/repository",
    tags=["Repository"]
)

@app.get("/")
def home():
    return {"message": "AI Senior Engineer API"}