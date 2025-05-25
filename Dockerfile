FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copiar apenas o requirements primeiro para cache eficiente
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r requirements.txt \
    --retries 10 --timeout 60 \
    --trusted-host pypi.org --trusted-host files.pythonhosted.org

# Agora sim copiar o restante
COPY . .

# Garantir que o diretório do modelo exista
RUN mkdir -p /models/ner-model

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["python", "main/main.py"]
