from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import stock
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Include routes with prefix /stock
app.include_router(stock.router, prefix="/stock")

# Serve static files (if needed)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Enable CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
