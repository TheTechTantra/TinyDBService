FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py auth.py crypto.py TinyDBUtil.py CredentialModel.py __init__.py ./

# Non-root user for reduced attack surface
RUN useradd --no-create-home --shell /bin/false appuser
USER appuser

EXPOSE 28080

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:28080/health')"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "28080"]
