#!/usr/bin/env bash
# Run management commands with exactly the same EnvironmentFile as the service.
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo 'Run with sudo.' >&2; exit 1; }
[[ $# -gt 0 ]] || { echo 'Usage: sudo bash deploy/ec2/manage.sh <Django command> [args]' >&2; exit 1; }
flags=(--wait --collect --service-type=exec --property=User=pasasa --property=Group=www-data
       --property=EnvironmentFile=/etc/pasasa/.env --working-directory=/opt/pasasa)
if [[ -t 0 && -t 1 ]]; then
    flags+=(--pty)
else
    flags+=(--pipe)
fi
exec systemd-run "${flags[@]}" /opt/pasasa/.venv/bin/python /opt/pasasa/manage.py "$@"
