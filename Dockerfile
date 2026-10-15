FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Optional extras: pass ORCHESTRA_EXTRAS=openai,anthropic at build time.
ARG ORCHESTRA_EXTRAS=""
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --upgrade pip \
    && if [ -n "$ORCHESTRA_EXTRAS" ]; then pip install ".[${ORCHESTRA_EXTRAS}]"; else pip install .; fi

RUN useradd --system --uid 10001 --create-home orchestra \
    && mkdir -p /data \
    && chown -R orchestra:orchestra /app /data
USER 10001:10001

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1

CMD ["uvicorn", "orchestra.api:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8000"]
