FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN apt-get update && apt-get install -y build-essential libffi-dev libpq-dev libssl-dev libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 libcairo2 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
