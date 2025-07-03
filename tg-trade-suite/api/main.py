from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()
app = FastAPI()

@app.get("/ping")
async def ping():
    return {"message": "pong"}
