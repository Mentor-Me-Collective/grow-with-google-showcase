FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as a non-root user for better container security
RUN useradd --create-home --uid 10001 appuser
USER appuser

# Shell form expands ${PORT}; exec passes SIGTERM cleanly to Uvicorn
CMD exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8080} --workers 1