from fastapi import FastAPI
from app.api import router

app = FastAPI(title="MS-DRG Provider API", version="1.0.0", description="Search providers and ask questions")
app.include_router(router, prefix="")
