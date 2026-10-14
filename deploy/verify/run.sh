#!/usr/bin/env bash
# Disposable container: validate Linux/PostgreSQL/Gunicorn/Nginx without an AWS account.
set -euo pipefail
cd /opt/pasasa
shellcheck deploy/ec2/*.sh deploy/verify/run.sh
for script in deploy/ec2/*.sh; do bash -n "$script"; done
pg_version=$(pg_lsclusters --no-header | awk 'NR==1 {print $1}')
pg_ctlcluster "$pg_version" main start
export POSTGRES_PASSWORD
POSTGRES_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
export DJANGO_SECRET_KEY
DJANGO_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_urlsafe(64))')
export DJANGO_SETTINGS_MODULE=PASASA.settings_cloud DJANGO_DEBUG=0 DJANGO_HTTPS=0
export DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,testserver
export POSTGRES_DB=pasasa POSTGRES_USER=pasasa POSTGRES_HOST=127.0.0.1 POSTGRES_PORT=5432
python3 <<'PY'
import os
import subprocess
password = os.environ['POSTGRES_PASSWORD']
# CREATEDB is only for Django's temporary test database in this disposable container.
sql = f"CREATE ROLE pasasa LOGIN CREATEDB PASSWORD '{password}';\nCREATE DATABASE pasasa OWNER pasasa;\n"
subprocess.run(['runuser', '-u', 'postgres', '--', 'psql', '-v', 'ON_ERROR_STOP=1'], input=sql, text=True, check=True)
with open('/etc/pasasa/.env', 'w') as stream:
    for key, value in os.environ.items():
        if key.startswith(('DJANGO_', 'POSTGRES_')):
            stream.write(f'{key}={value}\n')
os.chmod('/etc/pasasa/.env', 0o600)
PY
.venv/bin/python manage.py test --noinput
runuser -u postgres -- psql -v ON_ERROR_STOP=1 -c 'ALTER ROLE pasasa NOCREATEDB;'
.venv/bin/python manage.py migrate --noinput
.venv/bin/python manage.py seed_demo
.venv/bin/python manage.py seed_demo
.venv/bin/python manage.py makemigrations --check --dry-run
DJANGO_HTTPS=1 .venv/bin/python manage.py check --deploy
rsync -a media/ /var/lib/pasasa/media/
.venv/bin/python manage.py collectstatic --noinput
chown -R pasasa:www-data /var/lib/pasasa
install -m 0644 deploy/ec2/pasasa.service /etc/systemd/system/pasasa.service
systemd-analyze verify /etc/systemd/system/pasasa.service
sed 's/__PUBLIC_HOST__/pasasa.example.com/g' deploy/ec2/nginx.conf > /etc/nginx/sites-available/pasasa
ln -s /etc/nginx/sites-available/pasasa /etc/nginx/sites-enabled/pasasa
nginx -t
runuser -u pasasa -- .venv/bin/gunicorn --config deploy/ec2/gunicorn.conf.py PASASA.wsgi:application &
gunicorn_process=$!
trap 'kill "$gunicorn_process" 2>/dev/null || true' EXIT
nginx
curl --fail --silent --show-error --retry 10 --retry-connrefused --retry-delay 1 -H 'Host: localhost' http://127.0.0.1:8001/healthz/ | grep -q '"status": "ok"'
# localhost is explicitly allowed. Both requests go through the real Nginx proxy.
curl --fail --silent --show-error --retry 10 --retry-connrefused --retry-delay 1 -H 'Host: localhost' http://127.0.0.1/healthz/ | grep -q '"status": "ok"'
curl --fail --silent --show-error -H 'Host: localhost' http://127.0.0.1/catalog/maps/ | grep -q 'The Island'
curl --fail --silent --show-error -H 'Host: localhost' http://127.0.0.1/static/css/catalog.css >/dev/null
curl --fail --silent --show-error -H 'Host: localhost' http://127.0.0.1/media/maps/ISLANDpr.avif >/dev/null
echo 'LINUX VERIFICATION PASSED: PostgreSQL tests/migrations, deployment checks, systemd unit syntax, Gunicorn and Nginx HTTP/static/media.'
