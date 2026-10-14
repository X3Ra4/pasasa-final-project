# Local Linux validation only; EC2 deployment uses systemd, not Docker.
FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends python3-venv postgresql nginx systemd curl ca-certificates shellcheck rsync && rm -rf /var/lib/apt/lists/*
WORKDIR /opt/pasasa
COPY requirements.txt requirements-cloud.txt ./
RUN python3 -m venv .venv && .venv/bin/pip install --no-cache-dir -r requirements-cloud.txt
COPY . .
RUN useradd --system --home-dir /var/lib/pasasa --shell /usr/sbin/nologin pasasa && mkdir -p /var/lib/pasasa/media /var/lib/pasasa/static /etc/pasasa
CMD ["bash", "deploy/verify/run.sh"]
