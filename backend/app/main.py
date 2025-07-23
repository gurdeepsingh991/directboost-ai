from fastapi import FastAPI
from app.routers import segmentation
from app.routers import data_cleanup
from fastapi.middleware.cors import CORSMiddleware

app= FastAPI()

app.include_router(segmentation.router, prefix="/segment", tags=["segmentation"])
app.include_router(data_cleanup.router, prefix="/data-cleanup", tags=["uploadFile"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # or ["*"] for all origins (not recommended in prod)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

@app.get("/")
def read_root():
    return {"message": "Welcome!"}
