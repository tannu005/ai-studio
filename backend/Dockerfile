FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (e.g. for Pillow)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libopenjp2-7 \
    libtiff6 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV PORT=5000
ENV FLASK_ENV=production

CMD ["python", "run.py"]
