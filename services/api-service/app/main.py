from fastapi import FastAPI


app = FastAPI(title="Quant Research Platform")


@app.get("/health")
async def health_check():
    return {"status": "ok"}