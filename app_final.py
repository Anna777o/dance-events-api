from fastapi import FastAPI

app = FastAPI(title="Dance Studio Classes API")


@app.get("/")
def root():
    return {"message": "Dance Studio Classes API", "docs":
     "/docs"}