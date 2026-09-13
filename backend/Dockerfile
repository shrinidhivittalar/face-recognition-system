FROM python:3.11-slim

# opencv-python-headless still links libglib, but not libGL — the GUI stack a
# server never uses.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /srv

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ml ./ml
COPY models ./models
COPY backend/app ./backend/app
COPY scripts ./scripts

ENV PYTHONPATH=/srv:/srv/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--app-dir", "backend"]
