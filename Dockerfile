# Base image: Python 3.11-slim
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy files into container
COPY pdf_service.py requirements.txt ./

# Install dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    playwright install --with-deps chromium

# Expose default port
EXPOSE 8080

# Default command
ENTRYPOINT ["python", "pdf_service.py"]
