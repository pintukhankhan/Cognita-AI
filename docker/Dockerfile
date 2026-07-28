FROM python:3.11-slim AS b
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt
FROM python:3.11-slim
WORKDIR /app
COPY --from=b /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY src ./src
LABEL org.opencontainers.image.title="cognita"
RUN useradd -m -u 1000 app && chown -R app /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/v1/health/live')" || exit 1
CMD ["uvicorn","src.main:app","--host","0.0.0.0","--port","8000"]
