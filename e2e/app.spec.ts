import { test, expect, Page } from '@playwright/test';
import { mkdirSync } from 'node:fs';

const raw = { idMeal: '52772', strMeal: 'Teriyaki Chicken', strMealThumb: '', strCategory: 'Chicken', strArea: 'Japanese',
  strInstructions: 'Cook the chicken carefully. Serve with rice.', strIngredient1: 'Chicken', strMeasure1: '500 g', strIngredient2: 'Rice', strMeasure2: '200 g' };
async function mockApi(page: Page) {
  await page.route('**/api/json/v1/1/**', route => {
    const url = new URL(route.request().url());
    const body = url.pathname.endsWith('categories.php') ? { categories: [{ strCategory: 'Chicken' }, { strCategory: 'Vegetarian' }] }
      : { meals: url.searchParams.get('s') === 'noresults' ? null : [raw] };
    return route.fulfill({ json: body });
  });
}
async function start(page: Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'Почати готувати', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Відкрити рецепт Teriyaki Chicken' })).toBeVisible();
}

test('recipe to shopping, note, theme and storage survive reload and offline API', async ({ page }) => {
  const errors: string[] = []; page.on('pageerror', error => errors.push(error.message));
  await mockApi(page); await start(page);
  await page.getByRole('button', { name: 'Відкрити рецепт Teriyaki Chicken' }).click();
  await expect(page).toHaveURL(/meal\/52772/);
  await page.getByRole('textbox', { name: 'Нотатка до рецепта' }).fill('Менше солі');
  await page.getByRole('button', { name: 'Зберегти рецепт', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Прибрати з обраного' })).toBeVisible();
  await page.getByRole('button', { name: 'До списку покупок' }).click();
  await page.getByRole('button', { name: 'До списку покупок' }).click();
  await expect(page.getByRole('textbox', { name: 'Нотатка до рецепта' })).toHaveValue('Менше солі');
  await page.getByRole('button', { name: 'Зберегти нотатку' }).click();
  await page.goto('/shopping');
  await expect(page.getByRole('checkbox')).toHaveCount(2);
  await page.getByRole('checkbox', { name: 'Chicken, 500 g' }).click();
  await expect(page.getByRole('checkbox', { name: 'Chicken, 500 g' })).toBeChecked();
  await page.getByRole('button', { name: 'Додати продукт', exact: true }).click();
  await page.getByRole('button', { name: 'Зберегти продукт' }).click();
  await expect(page.getByText('Введіть назву продукту.')).toBeVisible();
  await page.getByRole('textbox', { name: 'Назва продукту' }).fill('Молоко');
  await page.getByRole('textbox', { name: 'Кількість', exact: true }).fill('1 л');
  await page.getByRole('button', { name: 'Зберегти продукт' }).click();
  await expect(page).toHaveURL(/\/shopping$/);
  await expect(page.getByRole('checkbox')).toHaveCount(3);
  await page.goto('/settings');
  await page.getByRole('switch', { name: 'Темна тема' }).click();
  await page.reload();
  await expect(page.getByRole('switch', { name: 'Темна тема' })).toBeChecked();
  await page.unroute('**/api/json/v1/1/**');
  await page.route('**/api/json/v1/1/**', route => route.abort());
  await page.goto('/saved');
  await page.getByRole('button', { name: 'Відкрити рецепт Teriyaki Chicken' }).click();
  await expect(page.getByText('Cook the chicken carefully. Serve with rice.')).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Нотатка до рецепта' })).toHaveValue('Менше солі');
  await page.getByRole('button', { name: 'Прибрати з обраного' }).click();
  await expect(page.getByText('Cook the chicken carefully. Serve with rice.')).toBeVisible();
  expect(errors).toEqual([]);
});

test('server search, empty and recoverable error states', async ({ page }) => {
  await mockApi(page); await start(page);
  await page.getByRole('textbox', { name: 'Пошук рецептів' }).fill('noresults');
  await page.getByRole('button', { name: 'Шукати', exact: true }).click();
  await expect(page.getByText('Ще не знайшли ваш рецепт')).toBeVisible();
  await page.unroute('**/api/json/v1/1/**');
  await page.route('**/api/json/v1/1/**', route => route.fulfill({ status: 503, body: '{}' }));
  await page.getByRole('textbox', { name: 'Пошук рецептів' }).fill('chicken');
  await page.getByRole('button', { name: 'Шукати', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Спробувати ще раз' })).toBeVisible();
  await page.unroute('**/api/json/v1/1/**'); await mockApi(page);
  await page.getByRole('button', { name: 'Спробувати ще раз' }).click();
  await expect(page.getByRole('button', { name: 'Відкрити рецепт Teriyaki Chicken' })).toBeVisible();
});

test('corrupt storage is recoverable only after explicit confirmation', async ({ page }) => {
  await mockApi(page); await page.goto('/');
  await page.evaluate(() => localStorage.setItem('@smak/state:v1', '{bad'));
  await page.reload(); await expect(page.getByText('Ваші дані важливі')).toBeVisible();
  expect(await page.evaluate(() => localStorage.getItem('@smak/state:v1'))).toBe('{bad');
  await page.getByRole('button', { name: 'Скинути локальні дані', exact: true }).click();
  expect(await page.evaluate(() => localStorage.getItem('@smak/state:v1'))).toBe('{bad');
  await page.getByRole('button', { name: 'Підтвердити видалення локальних даних' }).click();
  await expect(page.getByRole('button', { name: 'Почати готувати' })).toBeVisible();
});

test('real public API and screenshots in portrait, landscape and dark mode', async ({ page }) => {
  test.skip(!!process.env.CI, 'Live public API smoke is run locally; deterministic UI tests run in CI.');
  mkdirSync('screenshots', { recursive: true });
  await page.goto('/'); await expect(page.getByRole('button', { name: 'Почати готувати' })).toBeVisible();
  await page.waitForTimeout(600);
  await page.screenshot({ path: 'screenshots/01-onboarding.png' });
  await page.getByRole('button', { name: 'Почати готувати' }).click();
  const card = page.getByRole('button', { name: /^Відкрити рецепт / }).first();
  await expect(card).toBeVisible({ timeout: 20000 });
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'screenshots/02-discover.png' });
  await card.click();
  await expect(page.getByRole('button', { name: 'Зберегти рецепт', exact: true })).toBeVisible();
  await page.waitForTimeout(600);
  await page.screenshot({ path: 'screenshots/03-recipe.png' });
  await page.getByRole('button', { name: 'Зберегти рецепт', exact: true }).click();
  await page.getByRole('button', { name: 'До списку покупок' }).click();
  await page.goto('/shopping'); await expect(page.getByRole('checkbox').first()).toBeVisible();
  await page.screenshot({ path: 'screenshots/04-shopping.png' });
  await page.goto('/settings'); await page.getByRole('switch', { name: 'Темна тема' }).click();
  await page.goto('/saved'); await expect(page.getByRole('button', { name: /^Відкрити рецепт / }).first()).toBeVisible();
  await page.waitForTimeout(500); await page.screenshot({ path: 'screenshots/05-saved-dark.png' });
  await page.setViewportSize({ width: 844, height: 390 }); await page.goto('/');
  await expect(page.getByRole('button', { name: /^Відкрити рецепт / }).first()).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: 'screenshots/06-landscape.png' });
});
