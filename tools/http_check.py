"""Acceptance checks against an already running container stack; uses only stdlib.
Creates one disposable account, removes its temporary project, never prints credentials.
"""
import html
import http.cookiejar
import json
import os
import re
import secrets
from urllib.parse import urlencode, urljoin
from urllib.request import build_opener, HTTPCookieProcessor, Request

base = os.getenv('TASKFLOW_URL', 'http://127.0.0.1:8088').rstrip('/')
cookies = http.cookiejar.CookieJar()
client = build_opener(HTTPCookieProcessor(cookies))


def get(path):
    with client.open(urljoin(base, path), timeout=15) as response:
        assert response.status == 200
        return response.geturl(), response.read().decode()


def post(path, data):
    _, page = get(path)
    token = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', page).group(1)
    return submit(path, dict(data, csrfmiddlewaretoken=token))


def submit(path, data):
    if 'csrfmiddlewaretoken' not in data:
        data['csrfmiddlewaretoken'] = next(cookie.value for cookie in cookies if cookie.name == 'csrftoken')
    request = Request(urljoin(base, path), data=urlencode(data).encode(), headers={'Referer': base + path})
    with client.open(request, timeout=15) as response:
        assert response.status == 200
        return response.geturl(), response.read().decode()


assert json.loads(get('/healthz/')[1]) == {'status': 'ok'}
_, page = get('/accounts/login/')
for path in re.findall(r'<link[^>]+href="([^"]+)"', page):
    get(html.unescape(path))
name, password = 'http_' + secrets.token_hex(6), secrets.token_urlsafe(30)
url, _ = post('/accounts/signup/', {'username': name, 'password1': password, 'password2': password})
assert url == base + '/'
url, _ = post('/projects/new/', {'name': 'Container acceptance', 'description': 'HTTP through Nginx, Gunicorn and PostgreSQL'})
project_path = url.removeprefix(base)
url, _ = post(project_path + 'tasks/new/', {'title': 'HTTP test task', 'status': 'todo', 'priority': 'high'})
task_path = url.removeprefix(base)
_, page = submit(task_path + 'status/', {'status': 'done'})
assert 'status-pill done' in page
submit(task_path + 'comments/', {'body': 'Container verification'})
_, page = submit(task_path + 'archive/', {'archived': '1'})
assert 'В АРХІВІ' in page
submit(task_path + 'archive/', {'archived': '0'})
_, data = get('/api/tasks/')
# Browsable API is valid too; explicitly request JSON for the actual API assertion.
with client.open(Request(base + '/api/tasks/', headers={'Accept': 'application/json'})) as response:
    assert json.load(response)['count'] == 1
post(project_path + 'delete/', {})
submit('/accounts/logout/', {})
print('PASS: real HTTP health/static/signup/session/project/task/status/comment/archive/restore/API/delete/logout through container stack.')
