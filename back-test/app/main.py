from fastapi import FastAPI

from app.api.export import router

app = FastAPI()

app.include_router(router)