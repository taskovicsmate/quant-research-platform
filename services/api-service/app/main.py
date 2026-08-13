from fastapi import FastAPI

from app.db.database import engine, Base
from app.models.candle import Candle


Base.metadata.create_all(bind=engine)

app = FastAPI(title="Quant Research Platform")


@app.get("/health")
async def health_check():
    return {"status": "ok"}