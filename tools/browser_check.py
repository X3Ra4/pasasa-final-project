"""Optional end-to-end check. Run against a local, seeded development server."""
import os
import secrets
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PASASA.settings')
import django
django.setup()
from django.contrib.auth import get_user_model
from maps.models import Place
from playwright.sync_api import sync_playwright

base = os.environ.get('BROWSER_TEST_URL', 'http://127.0.0.1:8765')
screenshots = ROOT / 'screenshots'
screenshots.mkdir(exist_ok=True)
username = 'demo-' + secrets.token_hex(4)
password = secrets.token_urlsafe(24)
location_slug = 'browser-' + secrets.token_hex(5)
errors = []

try:
    with sync_playwright() as p:
        launch = {'headless': True}
        executable = os.environ.get('BROWSER_EXECUTABLE')
        if executable:
            launch['executable_path'] = executable
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
        page.on('pageerror', lambda error: errors.append(str(error)))
        for path, name in [('/catalog/maps/', '01-maps.png'), ('/catalog/places/', '02-locations.png'), ('/PVP/maps/the-island/', '03-interactive-map.png')]:
            response = page.goto(base + path)
            assert response.status == 200, path
            page.locator('h1').first.wait_for()
            page.locator('img').evaluate_all("imgs => imgs.forEach(img => img.loading = 'eager')")
            page.wait_for_function("Array.from(document.images).every(img => img.complete)")
            assert page.locator('img').evaluate_all('imgs => imgs.every(img => img.naturalWidth > 0)'), 'Broken image'
            page.screenshot(path=str(screenshots / name), full_page=True)
        page.goto(base + '/accounts/signup/')
        page.locator('[name=username]').fill(username)
        page.locator('[name=password1]').fill(password)
        page.locator('[name=password2]').fill(password)
        page.locator('main button[type=submit]').click()
        page.wait_for_url('**/catalog/places/')
        page.goto(base + '/catalog/places/new/')
        page.locator('[name=name]').fill('Demo forest base')
        page.locator('[name=slug]').fill(location_slug)
        page.locator('[name=map_location]').select_option(label='The Island')
        page.locator('[name=type]').select_option(label='Plain')
        page.locator('[name=coordsx]').fill('42.5')
        page.locator('[name=coordsy]').fill('61.0')
        page.locator('[name=rating]').fill('4')
        page.locator('[name=resources]').fill('5')
        page.screenshot(path=str(screenshots / '04-create-location.png'), full_page=True)
        page.get_by_role('button', name='Зберегти', exact=True).click()
        page.wait_for_url('**/catalog/places/*/')
        assert '/new/' not in page.url
        detail_url = page.url
        page.screenshot(path=str(screenshots / '05-location-detail.png'), full_page=True)
        page.get_by_role('link', name='Редагувати', exact=True).click()
        page.locator('[name=name]').fill('Updated forest base')
        page.get_by_role('button', name='Зберегти', exact=True).click()
        page.wait_for_url(detail_url)
        assert 'Updated forest base' in page.locator('h1').inner_text()
        page.get_by_role('link', name='Видалити', exact=True).click()
        page.get_by_role('button', name='Підтвердити видалення', exact=True).click()
        page.wait_for_url('**/catalog/places/')
        page.get_by_role('button', name='Вийти', exact=True).click()
        page.wait_for_url('**/PVP/maps/')
        page.goto(base + '/accounts/login/')
        page.locator('[name=username]').fill(username)
        page.locator('[name=password]').fill(password)
        page.locator('main button[type=submit]').click()
        page.wait_for_url('**/catalog/places/')
        page.set_viewport_size({'width': 390, 'height': 844})
        page.screenshot(path=str(screenshots / '06-mobile.png'), full_page=True)
        assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth'), 'Horizontal overflow on mobile'
        assert not errors, errors
        browser.close()
    print('Browser check passed: registration, login/logout, create/edit/delete, desktop/mobile and screenshots.')
finally:
    Place.objects.filter(slug=location_slug).delete()
    get_user_model().objects.filter(username=username).delete()
