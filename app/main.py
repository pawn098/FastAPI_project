from fastapi import FastAPI
from app.routers import category

app = FastAPI()

@app.get('/')
async def welcome() -> dict:
    return {"message": "My e-commerce app"}

app.include_router(category.router)