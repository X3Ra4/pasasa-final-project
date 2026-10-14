"""Create local Docker configuration once. Never print secrets or replace an existing file."""
from pathlib import Path
import secrets

target = Path(__file__).resolve().parent.parent / '.env'
content = (
    f'DJANGO_SECRET_KEY={secrets.token_urlsafe(64)}\n'
    'DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1\nDJANGO_HTTPS=0\n'
    'POSTGRES_DB=taskflow\nPOSTGRES_USER=taskflow\n'
    f'POSTGRES_PASSWORD={secrets.token_urlsafe(36)}\n'
    'TASKFLOW_BIND=127.0.0.1\nTASKFLOW_PORT=8088\n'
)
try:
    with target.open('x', encoding='utf-8') as handle:
        handle.write(content)
    target.chmod(0o600)
except FileExistsError:
    raise SystemExit('.env already exists; unchanged.')
print('Created .env for local Docker. Secrets are not printed.')
