from fastapi import FastAPI
from app.routers import segmentation, user_auth, booking_data, discounts, financials_data
from app.routers.models import train_test
from fastapi.middleware.cors import CORSMiddleware

app= FastAPI() 

app.include_router(segmentation.router, prefix="/segment", tags=["segmentation"])
app.include_router(booking_data.router, prefix="/process-bookings", tags=["uploadFile"])
app.include_router(user_auth.router, prefix="/auth", tags=["user_auth"])
app.include_router(train_test.router, prefix="/model", tags=["train_test"])
app.include_router(discounts.router, prefix="/discounts", tags=["discounts"])
app.include_router(financials_data.router, prefix="/financials", tags=["financials"])

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
