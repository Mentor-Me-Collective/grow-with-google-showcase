# Small, fast base image
FROM python:3.11-slim

# Prevents Python from writing .pyc files and buffering stdout (better for logs)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install dependencies first so this layer is cached unless requirements.txt changes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Make sure the notifications log file has somewhere to write
RUN mkdir -p /app/data

EXPOSE 5000

# Run with Flask's built-in server for the demo.
# (For real production use, swap this for gunicorn -- noted in README.)
CMD ["python", "app.py"]