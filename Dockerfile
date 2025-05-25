# Dockerfile
FROM base:latest

WORKDIR /app

COPY requirements.txt .

RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-cache-dir -r requirements.txt \
        --timeout 60 --retries 10 \
        --trusted-host pypi.org --trusted-host files.pythonhosted.org

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["python", "main/main.py"]
