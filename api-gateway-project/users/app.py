from fastapi import FastAPI
from typing import List

app = FastAPI()

# Endpoint per utenti
@app.get("/users", response_model=List[dict])
async def get_users():
    return [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]