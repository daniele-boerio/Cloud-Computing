import requests
import time

# Configurazione dell'API Gateway
API_GATEWAY_URL = "http://localhost:80"  # Cambia con l'URL del tuo API Gateway

# Funzione per ottenere il token JWT
def get_token():
    try:
        response = requests.post(f"{API_GATEWAY_URL}/token")
        response.raise_for_status()  # Solleva un'eccezione per status code 4xx/5xx
        return response.json().get("access_token")
    except requests.exceptions.RequestException as e:
        print(f"Error obtaining token: {e}")
        raise Exception("Error obtaining token")

# Funzione per testare gli endpoint protetti
def test_protected_endpoint(endpoint, token, retries=3, backoff=2):
    headers = {
        "Authorization": f"Bearer {token}"
    }
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(f"{API_GATEWAY_URL}/{endpoint}", headers=headers)
            response.raise_for_status()  # Solleva un'eccezione per status code 4xx/5xx
            return response
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed for {endpoint}: {e}")
            attempt += 1
            if attempt < retries:
                print(f"Retrying in {backoff ** attempt} seconds...")
                time.sleep(backoff ** attempt)
            else:
                print(f"Max retries reached for {endpoint}.")
                raise Exception(f"Failed to reach {endpoint} after {retries} attempts")

# Funzione per testare il bilanciamento del carico
def test_load_balancing(endpoint, token):
    instances = 5  # Numero di richieste per testare il bilanciamento del carico
    responses = []

    for i in range(instances):
        response = test_protected_endpoint(endpoint, token)
        responses.append(response)
        # Stampa lo status code e il contenuto del messaggio
        print(f"Request {i + 1}: Status Code {response.status_code}")
        print(f"Response Body: {response.text}")  # Stampa il corpo della risposta (come testo)
    
    return responses


# Funzione per testare tutto il sistema
def run_tests():
    try:
        # Ottieni il token JWT
        token = get_token()
        print(f"JWT Token: {token}")

        # Testa l'endpoint /users
        print("\nTesting /users endpoint...")
        users_responses = test_load_balancing("users", token)

        # Testa l'endpoint /products
        print("\nTesting /products endpoint...")
        products_responses = test_load_balancing("products", token)

        # Verifica che le risposte siano tutte valide
        for i, response in enumerate(users_responses):
            assert response.status_code == 200, f"User Request {i + 1} failed with status {response.status_code}"
        for i, response in enumerate(products_responses):
            assert response.status_code == 200, f"Product Request {i + 1} failed with status {response.status_code}"

        print("\nAll tests passed successfully!")

    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    run_tests()

#docker-compose down
#docker-compose up -d
