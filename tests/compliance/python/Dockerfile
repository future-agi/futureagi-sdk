FROM python:3.11-slim

WORKDIR /workspace

COPY python /workspace/python
COPY tests/compliance/python /workspace/tests/compliance/python

RUN pip install --no-cache-dir -e /workspace/python

ENV PYTHONPATH=/workspace/python
ENV PORT=8080

CMD ["python", "/workspace/tests/compliance/python/adapter.py"]
