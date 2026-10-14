"""Real browser acceptance test. Starts a local server; creates disposable users and a demo.
Run after migrate + collectstatic. Uses installed Chrome; no external browser service.
"""
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
OUT = ROOT / 'screenshots'
OUT.mkdir(exist_ok=True)
(ROOT / '.work').mkdir(exist_ok=True)
BASE = 'http://127.0.0.1:8767'
suffix = secrets.token_hex(4)
owner = 'olena_' + suffix
member = 'team_' + suffix
password = secrets.token_urlsafe(24)
errors = []


def signup(page, name):
    page.goto(BASE + '/accounts/signup/')
    page.locator('#id_username').fill(name)
    page.locator('#id_password1').fill(password)
    page.locator('#id_password2').fill(password)
    page.get_by_role('button', name='Зареєструватися', exact=True).click()
    expect(page).to_have_url(BASE + '/')


with (ROOT / '.work/browser-server.log').open('w', encoding='utf-8') as log:
    server = subprocess.Popen([sys.executable, 'manage.py', 'runserver', '127.0.0.1:8767', '--noreload'],
                              stdout=log, stderr=log,
                              creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
    try:
        for _ in range(50):
            try:
                with urlopen(BASE + '/healthz/', timeout=1) as response:
                    if response.status == 200:
                        break
            except OSError:
                time.sleep(.2)
        else:
            raise RuntimeError('Server not ready')
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel='chrome', headless=True)
            context = browser.new_context(viewport={'width': 1440, 'height': 1000}, locale='uk-UA')
            page = context.new_page()
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.goto(BASE + '/accounts/login/')
            page.screenshot(path=str(OUT / '01-login.png'), full_page=True)
            signup(page, owner)
            subprocess.run([sys.executable, 'manage.py', 'seed_demo', '--owner', owner], check=True, capture_output=True)
            page.reload()
            page.screenshot(path=str(OUT / '02-dashboard.png'), full_page=True)
            page.get_by_role('link', name='Запуск нового продукту', exact=True).click()
            page.screenshot(path=str(OUT / '03-board.png'), full_page=True)
            demo_url = page.url
            page.get_by_role('link', name='Розробити REST API завдань', exact=True).click()
            page.screenshot(path=str(OUT / '04-task.png'), full_page=True)
            page.set_viewport_size({'width': 390, 'height': 844})
            page.goto(demo_url)
            assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Mobile horizontal overflow'
            page.screenshot(path=str(OUT / '05-mobile.png'), full_page=True)
            page.set_viewport_size({'width': 1440, 'height': 1000})
            page.locator('nav a[href="/projects/new/"]').click()
            page.locator('#id_name').fill('Browser acceptance')
            page.locator('#id_description').fill('Project created through the actual browser')
            page.get_by_role('button', name='Зберегти', exact=True).click()
            project_url = page.url
            member_context = browser.new_context()
            member_page = member_context.new_page()
            signup(member_page, member)
            page.get_by_role('link', name='Команда', exact=True).click()
            page.locator('#id_username').fill(member)
            page.get_by_role('button', name='Додати до команди').click()
            expect(page.locator('.member-row').filter(has_text=member)).to_be_visible()
            page.goto(project_url)
            page.get_by_role('link', name='＋ Нове завдання', exact=True).click()
            page.locator('#id_title').fill('Browser task')
            page.locator('#id_description').fill('Verify CRUD, roles and comments')
            page.locator('#id_assignee').select_option(label=member)
            page.locator('#id_priority').select_option('high')
            page.locator('#id_due_date').fill('2026-12-31')
            page.get_by_role('button', name='Зберегти', exact=True).click()
            task_url = page.url
            member_page.goto(task_url)
            member_page.locator('#id_status').select_option('doing')
            member_page.get_by_role('button', name='Змінити статус').click()
            expect(member_page.locator('.status-pill')).to_have_text('У роботі')
            member_page.locator('#id_body').fill('Member feedback through the browser')
            member_page.get_by_role('button', name='Додати коментар').click()
            expect(member_page.locator('.comment')).to_contain_text('Member feedback through the browser')
            assert member_page.get_by_role('link', name='Редагувати', exact=True).count() == 0
            page.reload()
            page.get_by_role('link', name='Редагувати', exact=True).click()
            page.locator('#id_title').fill('Browser task edited')
            page.get_by_role('button', name='Зберегти', exact=True).click()
            expect(page.get_by_role('heading', level=1)).to_have_text('Browser task edited')
            page.get_by_role('button', name='Архівувати', exact=True).click()
            expect(page.locator('.eyebrow')).to_contain_text('В АРХІВІ')
            page.get_by_role('button', name='Відновити з архіву').click()
            page.get_by_role('link', name='Видалити завдання', exact=True).click()
            page.get_by_role('button', name='Так, видалити').click()
            expect(page).to_have_url(project_url)
            page.get_by_role('link', name='Налаштування', exact=True).click()
            page.get_by_role('link', name='Видалити проєкт', exact=True).click()
            page.get_by_role('button', name='Так, видалити').click()
            page.get_by_role('button', name='Вийти', exact=True).click()
            page.locator('#id_username').fill(owner)
            page.locator('#id_password').fill(password)
            page.get_by_role('button', name='Увійти →', exact=True).click()
            expect(page).to_have_url(BASE + '/')
            assert not errors, errors
            browser.close()
        print('PASS: signup/login/logout, project/task CRUD, membership, assignee status, comment, archive/restore, mobile, no JS errors; 5 screenshots.')
    finally:
        server.terminate()
        server.wait(timeout=10)
