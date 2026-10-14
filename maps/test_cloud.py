import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

from django.db import DatabaseError
from django.test import SimpleTestCase, TestCase

ROOT = Path(__file__).resolve().parent.parent


class CloudSettingsTests(SimpleTestCase):
    def settings_process(self, **changes):
        env = {key: value for key, value in os.environ.items() if not key.startswith(('DJANGO_', 'POSTGRES_'))}
        env.update(DJANGO_SETTINGS_MODULE='PASASA.settings_cloud', DJANGO_DEBUG='0',
                   DJANGO_SECRET_KEY='cloud-test-only-secret-' * 4,
                   DJANGO_ALLOWED_HOSTS='pasasa.example.com, localhost',
                   POSTGRES_DB='pasasa', POSTGRES_USER='pasasa', POSTGRES_PASSWORD='test-only',
                   POSTGRES_HOST='127.0.0.1', POSTGRES_PORT='5432')
        for key, value in changes.items():
            if value is None:
                env.pop(key, None)
            else:
                env[key] = value
        code = '''import json
from django.conf import settings as s
print(json.dumps(dict(debug=s.DEBUG, engine=s.DATABASES['default']['ENGINE'], host=s.DATABASES['default']['HOST'], hosts=s.ALLOWED_HOSTS, https=s.SECURE_SSL_REDIRECT, cookie=s.SESSION_COOKIE_SECURE, media=str(s.MEDIA_ROOT))))
'''
        return subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=env, text=True, capture_output=True)

    def test_cloud_uses_postgres_and_secure_defaults(self):
        result = self.settings_process()
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(data['engine'], 'django.db.backends.postgresql')
        self.assertEqual(data['host'], '127.0.0.1')
        self.assertEqual(data['hosts'], ['pasasa.example.com', 'localhost'])
        self.assertFalse(data['debug'])
        self.assertTrue(data['https'])
        self.assertTrue(data['cookie'])
        self.assertEqual(data['media'].replace('\\', '/'), '/var/lib/pasasa/media')

    def test_cloud_rejects_missing_secrets_or_hosts(self):
        for key in ['DJANGO_SECRET_KEY', 'POSTGRES_PASSWORD', 'POSTGRES_HOST', 'DJANGO_ALLOWED_HOSTS']:
            with self.subTest(key=key):
                result = self.settings_process(**{key: None})
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(key, result.stderr)

    def test_cloud_rejects_debug_and_wildcard_host(self):
        for changes in [{'DJANGO_DEBUG': '1'}, {'DJANGO_ALLOWED_HOSTS': '*'}]:
            self.assertNotEqual(self.settings_process(**changes).returncode, 0)

    def test_explicit_http_demo_keeps_login_working(self):
        result = self.settings_process(DJANGO_HTTPS='0')
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertFalse(data['https'])
        self.assertFalse(data['cookie'])


class HealthTests(TestCase):
    def test_database_health(self):
        response = self.client.get('/healthz/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok'})
        self.assertIn('no-store', response['Cache-Control'])

    def test_database_failure_is_503_without_details(self):
        with patch('django.db.backends.utils.CursorWrapper.execute', side_effect=DatabaseError('private connection details')):
            response = self.client.get('/healthz/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json(), {'status': 'unavailable'})
        self.assertNotContains(response, 'private', status_code=503)
