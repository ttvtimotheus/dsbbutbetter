FROM python:3.9-slim

WORKDIR /app

# Systemabhängigkeiten für easyOCR und andere Bibliotheken installieren
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    ffmpeg \
    libsm6 \
    libxext6 \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Pytorch und Torchvision vorinstallieren (für easyOCR)
RUN pip install torch==2.0.1 torchvision==0.15.2 --index-url https://download.pytorch.org/whl/cpu

# Anforderungen kopieren und installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Erstellen der notwendigen Verzeichnisse
RUN mkdir -p logs

# Kopieren des Backend-Codes
COPY . .

# Sicherstellen, dass der Logs-Ordner existiert
RUN mkdir -p logs

# Ausführen der Anwendung
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
