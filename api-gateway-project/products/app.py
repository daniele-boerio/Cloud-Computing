from fastapi import FastAPI
from typing import List

app = FastAPI()

# Endpoint per prodotti
@app.get("/products", response_model=List[dict])
def get_products():
    return [{"id": 1, "name": "Laptop"}, {"id": 2, "name": "Phone"}]
