from fastapi import FastAPI

app = FastAPI(title="Narrative Nexus")

@app.get("/health")
def health():
    return {"status": "ok"}
