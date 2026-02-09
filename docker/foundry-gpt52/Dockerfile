FROM python:3.11-slim

WORKDIR /app

# Keep image small and deterministic
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN pip install --no-cache-dir openai azure-identity

COPY main.py /app/main.py

CMD ["python", "/app/main.py"]
