FROM python:3.12-slim

# Injected at build time: docker build --build-arg GIT_COMMIT=$(git rev-parse --short HEAD)
ARG GIT_COMMIT=unknown

# OCI standard image labels — visible via `docker inspect`
LABEL org.opencontainers.image.source="https://github.com/thetechtantra/TinyDBService" \
      org.opencontainers.image.revision="${GIT_COMMIT}" \
      org.opencontainers.image.title="TinyDBService" \
      org.opencontainers.image.description="Encrypted key/value credential store"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py auth.py crypto.py TinyDBUtil.py CredentialModel.py __init__.py ./

# Bake SHA into the image so /health can report it at runtime
ENV APP_VERSION=${GIT_COMMIT}

# Non-root user for reduced attack surface
RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

EXPOSE 28080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:28080/health')"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "28080"]
