FROM python:3.11-slim

WORKDIR /app

# Heavy deps (torch, chromadb) — cached separately so they don't re-download on every change
COPY requirements-heavy.txt .
RUN pip install --no-cache-dir -r requirements-heavy.txt

# Light deps — reinstalls quickly when requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
