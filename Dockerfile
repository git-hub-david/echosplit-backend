FROM python:3.9-slim

# Install ffmpeg (required by Demucs) and git (Demucs may pull models)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg git && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY handler.py .

# Env vars are injected at runtime
ENV AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
ENV AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
ENV AWS_REGION=${AWS_REGION}
ENV S3_BUCKET=${S3_BUCKET}

# Demucs listens via handler(), RunPod defaults to port 8080
EXPOSE 8080

CMD ["python", "handler.py"]