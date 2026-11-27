from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
import models
from routes import auth, chat, shifts

# Create SQLite tables automatically on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="ShiftBridge API", version="1.0.0")

app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(shifts.router)

origins = [
    "http://localhost:5173",
    "http://ihesami.github.io/shiftBridge-UI",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "healthy", "service": "ShiftBridge API"}