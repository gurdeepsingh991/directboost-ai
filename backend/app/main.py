from fastapi import FastAPI
from app.routers import segmentation

app= FastAPI(title:"Direct Boost AI Backend")

app.include_router(segmentation.router, prefix="/segment", tags=["segmentation"])


@app.get("/")
def read_root():
    return {"message": "Welcome!"}
