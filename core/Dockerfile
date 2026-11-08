FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates iputils-ping libcap2-bin \
    && setcap cap_net_raw+ep /usr/bin/ping \
    && apt-get purge -y libcap2-bin \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system --gid 10001 sentinel \
    && useradd --system --uid 10001 --gid sentinel --home-dir /app --no-create-home sentinel \
    && mkdir -p /data \
    && chown sentinel:sentinel /data

WORKDIR /app

COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY scripts ./scripts

USER 10001:10001
EXPOSE 18101
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "18101", "--proxy-headers", "--forwarded-allow-ips", "*"]
