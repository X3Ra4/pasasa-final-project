#!/usr/bin/env bash
# First installation on a dedicated Ubuntu 24.04 EC2 instance.
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Run with sudo.' >&2; exit 1; }
public_host=${1:-}
[[ $public_host =~ ^[A-Za-z0-9][A-Za-z0-9.-]*$ ]] || { echo 'Pass one public DNS name or IPv4 address (without http:// or a port).' >&2; exit 1; }
# shellcheck source=/dev/null
source /etc/os-release
[[ $ID == ubuntu && $VERSION_ID == 24.04 ]] || { echo 'This script requires Ubuntu 24.04.' >&2; exit 1; }
[[ ! -e /opt/pasasa && ! -e /etc/pasasa/.env ]] || { echo 'An installation already exists. Use update.sh; no files were overwritten.' >&2; exit 1; }
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y python3-venv python3-pip postgresql nginx git rsync curl
systemctl enable --now postgresql
id pasasa >/dev/null 2>&1 || useradd --system --home-dir /var/lib/pasasa --shell /usr/sbin/nologin pasasa
install -d -o root -g pasasa -m 0750 /etc/pasasa
install -d -o pasasa -g www-data -m 0750 /var/lib/pasasa /var/lib/pasasa/media /var/lib/pasasa/static
git clone --branch cloud-solutions-aws --single-branch https://github.com/X3Ra4/pasasa-final-project.git /opt/pasasa
python3 -m venv /opt/pasasa/.venv
/opt/pasasa/.venv/bin/python -m pip install -r /opt/pasasa/requirements-cloud.txt

# Random values never appear in command arguments or stdout.
python3 - "$public_host" <<'PY'
import os
import secrets
import subprocess
import sys
from pathlib import Path

host = sys.argv[1]
password = secrets.token_hex(32)
secret = secrets.token_urlsafe(64)
# Refuse to change a pre-existing database or role on this machine.
probe = subprocess.run(['runuser', '-u', 'postgres', '--', 'psql', '-tAc',
                        "SELECT EXISTS(SELECT FROM pg_roles WHERE rolname='pasasa') OR EXISTS(SELECT FROM pg_database WHERE datname='pasasa')"],
                       check=True, capture_output=True, text=True)
if probe.stdout.strip() != 'f':
    raise SystemExit('Database or role pasasa already exists; refusing to overwrite it.')
sql = f"CREATE ROLE pasasa LOGIN PASSWORD '{password}';\nCREATE DATABASE pasasa OWNER pasasa;\n"
subprocess.run(['runuser', '-u', 'postgres', '--', 'psql', '-v', 'ON_ERROR_STOP=1'], input=sql, text=True, check=True, stdout=subprocess.DEVNULL)
values = {
    'DJANGO_SETTINGS_MODULE': 'PASASA.settings_cloud', 'DJANGO_DEBUG': '0',
    'DJANGO_SECRET_KEY': secret, 'DJANGO_ALLOWED_HOSTS': f'{host},127.0.0.1,localhost',
    'DJANGO_HTTPS': '0', 'DJANGO_CSRF_TRUSTED_ORIGINS': f'http://{host}',
    'POSTGRES_DB': 'pasasa', 'POSTGRES_USER': 'pasasa', 'POSTGRES_PASSWORD': password,
    'POSTGRES_HOST': '127.0.0.1', 'POSTGRES_PORT': '5432',
    'DJANGO_STATIC_ROOT': '/var/lib/pasasa/static', 'DJANGO_MEDIA_ROOT': '/var/lib/pasasa/media',
}
fd = os.open('/etc/pasasa/.env', os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as stream:
    stream.writelines(f'{key}={value}\n' for key, value in values.items())
PY
chown root:pasasa /etc/pasasa/.env
chmod 0640 /etc/pasasa/.env
rsync -a --ignore-existing /opt/pasasa/media/ /var/lib/pasasa/media/
chown -R pasasa:www-data /var/lib/pasasa
chmod -R u=rwX,g=rX,o= /var/lib/pasasa
bash /opt/pasasa/deploy/ec2/manage.sh migrate --noinput
bash /opt/pasasa/deploy/ec2/manage.sh seed_demo
bash /opt/pasasa/deploy/ec2/manage.sh collectstatic --noinput
install -m 0644 /opt/pasasa/deploy/ec2/pasasa.service /etc/systemd/system/pasasa.service
sed "s/__PUBLIC_HOST__/$public_host/g" /opt/pasasa/deploy/ec2/nginx.conf > /etc/nginx/sites-available/pasasa
ln -s /etc/nginx/sites-available/pasasa /etc/nginx/sites-enabled/pasasa
if [[ -L /etc/nginx/sites-enabled/default && $(readlink /etc/nginx/sites-enabled/default) == /etc/nginx/sites-available/default ]]; then
    unlink /etc/nginx/sites-enabled/default
fi
nginx -t
systemctl daemon-reload
systemctl enable --now pasasa nginx
systemctl reload nginx
curl --fail --retry 10 --retry-connrefused --retry-delay 2 -H "Host: $public_host" http://127.0.0.1/healthz/
echo
echo 'Installed. Configure HTTPS before using real accounts. See docs/CLOUD_DEPLOYMENT.md.'
