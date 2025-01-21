from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
import jwt
from jwt.exceptions import PyJWTError
from pydantic import BaseModel
import time
import logging
import httpx
from pybreaker import CircuitBreaker

# Definizione dell'app FastAPI
app = FastAPI()

SECRET_KEY = "mysecretkey"
ALGORITHM = "HS256"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Configurazione di base del logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Impostazioni per il circuit breaker
circuit_breaker = CircuitBreaker(fail_max=3, reset_timeout=30)

# Funzione per verificare il JWT con tolleranza ai guasti
def verify_token(token: str = Depends(oauth2_scheme)):
    retries = 3
    for attempt in range(retries):
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            return payload
        except PyJWTError as e:
            logger.error(f"Error decoding token on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                time.sleep(1)  # Ritenta dopo 1 secondo
            else:
                raise HTTPException(
                    status_code=401,
                    detail="Could not validate credentials",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {e}")
            raise HTTPException(
                status_code=500,
                detail="Internal server error during token verification",
            )

# Funzione per creare un token di accesso con tolleranza ai guasti
def create_access_token(data: dict):
    retries = 3
    for attempt in range(retries):
        try:
            token = jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)
            return token
        except Exception as e:
            logger.error(f"Error creating token on attempt {attempt + 1}: {e}")
            if attempt < retries - 1:
                time.sleep(1)  # Ritenta dopo 1 secondo
            else:
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error while creating token"
                )

# Pydantic model per il login
class Token(BaseModel):
    access_token: str
    token_type: str

# Endpoint per ottenere il token
@app.post("/token", response_model=Token)
def login_for_access_token():
    try:
        # In un'applicazione reale, dovresti verificare le credenziali dell'utente
        token = create_access_token(data={"sub": "user"})
        return {"access_token": token, "token_type": "bearer"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during login")

# Funzione protetta da CircuitBreaker per chiamare il microservizio
async def fetch_with_circuit_breaker(url: str):
    async with httpx.AsyncClient(timeout=httpx.Timeout(10.0)) as client:
        response = await client.get(url)
    return response

# Endpoint protetto da JWT con tolleranza ai guasti
@app.get("/users")
async def get_users(current_user: dict = Depends(verify_token)):
    try:
        # Usa il circuit breaker per proteggere la chiamata al microservizio
        @circuit_breaker
        async def fetch_users():
            microservice_url = "http://users:3001/users"
            return await fetch_with_circuit_breaker(microservice_url)
        
        # Chiama la funzione protetta dal CircuitBreaker
        response = await fetch_users()
        
        # Verifica se la risposta del microservizio è positiva
        if response.status_code == 200:
            return response.json()  # Restituisci il contenuto della risposta del microservizio come JSON
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error from microservice: {response.text}"
            )

    except httpx.RequestError as e:
        # Gestisce eventuali errori durante la comunicazione con il microservizio
        logger.error(f"Request error while accessing microservice /users: {e}")
        raise HTTPException(status_code=502, detail="Bad gateway, failed to reach the microservice")

    except Exception as e:
        # Gestisce qualsiasi altro tipo di errore
        logger.error(f"Unexpected error while accessing /users: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while accessing users")

# Endpoint protetto da JWT con tolleranza ai guasti
@app.get("/products")
async def get_products(current_user: dict = Depends(verify_token)):
    try:
        # Usa il circuit breaker per proteggere la chiamata al microservizio
        @circuit_breaker
        async def fetch_products():
            microservice_url = "http://products:3002/products"
            return await fetch_with_circuit_breaker(microservice_url)
        
        # Chiama la funzione protetta dal CircuitBreaker
        response = await fetch_products()
        
        # Verifica se la risposta del microservizio è positiva
        if response.status_code == 200:
            return response.json()  # Restituisci il contenuto della risposta del microservizio come JSON
        else:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Error from microservice: {response.text}"
            )

    except httpx.RequestError as e:
        # Gestisce eventuali errori durante la comunicazione con il microservizio
        logger.error(f"Request error while accessing microservice /products: {e}")
        raise HTTPException(status_code=502, detail="Bad gateway, failed to reach the microservice")

    except Exception as e:
        # Gestisce qualsiasi altro tipo di errore
        logger.error(f"Unexpected error while accessing /products: {e}")
        raise HTTPException(status_code=500, detail="Internal server error while accessing products")
