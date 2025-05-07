from fastapi import FastAPI

app = FastAPI()

@app.get("/ingest")
def read_root():
    return {"Hello": "World"}