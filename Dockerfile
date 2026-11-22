# ==============================================================================
# AuraLink Mobile Free Keys Admin Backend — Production Dockerfile (Railway-ready)
# ==============================================================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8088

WORKDIR /app

# Install Python dependencies first for optimal Docker layer caching
COPY mobile_backend/requirements.txt /app/mobile_backend/requirements.txt
RUN pip install --no-cache-dir -r /app/mobile_backend/requirements.txt

# Copy only the mobile admin backend package
COPY mobile_backend /app/mobile_backend

# Prepare default persistent volume mount point for Railway Volume (/data)
RUN mkdir -p /data

EXPOSE 8088

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import os, urllib.request; p = os.environ.get('PORT', '8088'); urllib.request.urlopen(f'http://127.0.0.1:{p}/api/health', timeout=3)" || exit 1

CMD ["python", "-m", "mobile_backend.run"]
