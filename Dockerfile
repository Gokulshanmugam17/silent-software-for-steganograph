# Dockerfile for SILENT Steganography Project on Render
FROM python:3.10-slim

# Install system dependencies including ffmpeg for audio/video processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Ensure the upload directory exists
RUN mkdir -p web_app/uploads

# Expose the port (Render handles this, but good to have)
EXPOSE 8080

# Run with Gunicorn for production
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "web_app.app:app"]
