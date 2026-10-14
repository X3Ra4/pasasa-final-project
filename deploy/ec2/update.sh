#!/usr/bin/env bash
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Run with sudo.' >&2; exit 1; }
exec 9>/run/lock/pasasa-deploy.lock
flock -n 9 || { echo 'Another deployment is running.' >&2; exit 1; }
cd /opt/pasasa
[[ $(git branch --show-current) == cloud-solutions-aws ]] || { echo 'Wrong branch.' >&2; exit 1; }
[[ -z $(git status --porcelain) ]] || { echo 'Working tree is not clean; refusing to overwrite edits.' >&2; exit 1; }
# Stop before changing code or dependencies so requests never see a mixed release.
systemctl stop pasasa
trap 'systemctl start pasasa' EXIT
git pull --ff-only origin cloud-solutions-aws
.venv/bin/python -m pip install -r requirements-cloud.txt
# Keep existing media, secrets and database.
bash deploy/ec2/manage.sh migrate --noinput
bash deploy/ec2/manage.sh collectstatic --noinput
rsync -a --ignore-existing media/ /var/lib/pasasa/media/
chown -R pasasa:www-data /var/lib/pasasa
chmod -R u=rwX,g=rX,o= /var/lib/pasasa
install -m 0644 deploy/ec2/pasasa.service /etc/systemd/system/pasasa.service
systemctl daemon-reload
systemctl start pasasa
trap - EXIT
curl --fail --retry 10 --retry-connrefused --retry-delay 2 -H 'X-Forwarded-Proto: https' http://127.0.0.1:8001/healthz/ | grep -q '"status": "ok"'
echo
echo 'Updated. Review Nginx changes separately so an existing HTTPS configuration is preserved.'
