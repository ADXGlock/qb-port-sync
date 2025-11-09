# ================================
# qb-port-sync Dockerfile
# ================================
# Base image
FROM python:3.12-slim

# Prevent Python from writing pyc files and buffer logs
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Working directory
WORKDIR /app

# --------------------------------
# Install dependencies (system + Python)
# --------------------------------
# Install curl for healthcheck and lightweight debugging
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Copy dependency list and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --------------------------------
# Copy application code
# --------------------------------
COPY update_qb_port.py /app/

# --------------------------------
# Healthcheck (optional but recommended)
# --------------------------------
# If you include this in the image itself (can also define in docker-compose)
HEALTHCHECK --interval=40s --timeout=30s --retries=3 --start-period=60s \
  CMD curl --fail http://ifconfig.me/ || exit 1

# --------------------------------
# Default command
# --------------------------------
CMD ["python", "-u", "/app/update_qb_port.py"]

