FROM python:3.10-slim

# Install system tools
RUN apt update && apt install -y git ffmpeg

# Install Demucs
RUN pip install demucs

# Set working directory
WORKDIR /app

# Copy project files
COPY . .

# Install Python packages
RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python", "handler.py"]