# 1. Base image with Python 3.10 (slim for minimal size)
FROM python:3.10-slim

# 2. Install system dependencies for Demucs:
#    - git:     required by some models
#    - ffmpeg:  for audio decoding/encoding
RUN apt update && apt install -y git ffmpeg && \
    apt clean && rm -rf /var/lib/apt/lists/*

# 3. Install Demucs and DiffQ (required by the mdx_extra_q model)
RUN pip install demucs diffq

# 4. Set working directory for your app
WORKDIR /app

# 5. Copy your backend code and dependencies list
COPY . .

# 6. Install Python dependencies from requirements.txt:
#    Flask, boto3, python-dotenv
RUN pip install -r requirements.txt

# 7. Expose port 5000 so RunPod can route traffic
EXPOSE 5000

# 8. Start your Flask handler on container launch
CMD ["python", "handler.py"]