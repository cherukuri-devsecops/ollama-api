FROM python:3.12-slim

WORKDIR /app

# Create non-root user for security
RUN useradd -m -u 1000 appuser

COPY requirements.txt .
RUN mkdir -p /app && \
    chown -R appuser:appuser /app && \
    pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

ARG GIT_SHA
ENV GIT_SHA=$GIT_SHA

ENV OLLAMA_BASE_URL=http://ollama:11434

EXPOSE 8000

# Switch to non-root user
USER appuser

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
