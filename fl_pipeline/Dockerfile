FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++ && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Assemble NVFlare job folder: job/meta.json + job/app/ (config & custom)
RUN mkdir -p /app/job && cp /app/meta.json /app/job/ && cp -r /app/app /app/job/app
# Make custom/ importable so NVFlare can resolve "custom.densenet_square" etc.
ENV PYTHONPATH="/app/job/app:${PYTHONPATH}"
CMD ["python", "run_simulator.py"]
