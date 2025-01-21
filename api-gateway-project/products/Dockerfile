# Usa un'immagine base Python
FROM python:3.9-slim

# Imposta la directory di lavoro
WORKDIR /app

# Copia i file del microservizio
COPY . /app

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Esponi la porta
EXPOSE 3002

# Comando per avviare il microservizio
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "3002"]
