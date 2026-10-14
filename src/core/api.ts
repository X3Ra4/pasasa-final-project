import { Ingredient, Meal, MealSummary } from './types';

const BASE = 'https://www.themealdb.com/api/json/v1/1';
type Fetcher = (url: string, init?: RequestInit) => Promise<Response>;
const text = (value: unknown) => typeof value === 'string' ? value.trim() : '';
export function safeUrl(value: unknown): string {
  const url = text(value);
  return /^https:\/\//i.test(url) ? url : '';
}
function record(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Невірний формат відповіді сервера.');
  return value as Record<string, unknown>;
}
function summary(value: unknown): MealSummary {
  const raw = record(value);
  const id = text(raw.idMeal), name = text(raw.strMeal);
  if (!/^\d+$/.test(id) || !name) throw new Error('Сервер повернув некоректний рецепт.');
  return { id, name, image: safeUrl(raw.strMealThumb),
    ...(text(raw.strCategory) ? { category: text(raw.strCategory) } : {}),
    ...(text(raw.strArea) ? { area: text(raw.strArea) } : {}) };
}
export function normalizeSummaries(value: unknown): MealSummary[] {
  if (value === null) return [];
  if (!Array.isArray(value)) throw new Error('Невірний формат списку рецептів.');
  return value.map(summary).filter((meal, index, all) => all.findIndex(item => item.id === meal.id) === index);
}
export function normalizeMeal(value: unknown): Meal {
  const raw = record(value);
  const base = summary(raw);
  const ingredients: Ingredient[] = [];
  for (let index = 1; index <= 20; index++) {
    const name = text(raw[`strIngredient${index}`]);
    if (name) ingredients.push({ name, amount: text(raw[`strMeasure${index}`]) });
  }
  if (!text(raw.strInstructions) || !ingredients.length) throw new Error('У рецепті відсутні інструкції або інгредієнти.');
  return { ...base, ingredients, instructions: text(raw.strInstructions), source: safeUrl(raw.strSource), video: safeUrl(raw.strYoutube) };
}
async function request(path: string, signal?: AbortSignal, fetcher: Fetcher = fetch) {
  const controller = new AbortController();
  let timeout = false;
  const abort = () => controller.abort();
  signal?.addEventListener('abort', abort);
  if (signal?.aborted) controller.abort();
  const timer = setTimeout(() => { timeout = true; controller.abort(); }, 12000);
  try {
    const response = await fetcher(`${BASE}/${path}`, { signal: controller.signal });
    if (!response.ok) throw new Error(`Сервіс рецептів тимчасово недоступний (${response.status}).`);
    return record(await response.json());
  } catch (error) {
    if (signal?.aborted) { const cancelled = new Error('Cancelled'); cancelled.name = 'AbortError'; throw cancelled; }
    if (timeout) throw new Error('Сервер не відповідає. Перевірте мережу та спробуйте ще раз.');
    if (error instanceof Error && error.message.startsWith('Сервіс')) throw error;
    throw new Error('Не вдалося отримати дані. Перевірте інтернет і повторіть запит.');
  } finally {
    clearTimeout(timer); signal?.removeEventListener('abort', abort);
  }
}
export async function searchMeals(filter: { query?: string; category?: string }, signal?: AbortSignal, fetcher?: Fetcher) {
  const path = filter.category ? `filter.php?c=${encodeURIComponent(filter.category)}` : `search.php?s=${encodeURIComponent(filter.query?.trim() ?? '')}`;
  const data = await request(path, signal, fetcher);
  return normalizeSummaries(data.meals);
}
export async function getMeal(id: string, signal?: AbortSignal, fetcher?: Fetcher): Promise<Meal | null> {
  if (!/^\d{1,12}$/.test(id)) throw new Error('Некоректний ідентифікатор рецепта.');
  const data = await request(`lookup.php?i=${encodeURIComponent(id)}`, signal, fetcher);
  if (data.meals === null || (Array.isArray(data.meals) && !data.meals.length)) return null;
  if (!Array.isArray(data.meals)) throw new Error('Невірний формат рецепта.');
  const meal = normalizeMeal(data.meals[0]);
  if (meal.id !== id) throw new Error('Сервер повернув інший рецепт.');
  return meal;
}
export async function getCategories(signal?: AbortSignal, fetcher?: Fetcher): Promise<string[]> {
  const data = await request('categories.php', signal, fetcher);
  if (!Array.isArray(data.categories)) throw new Error('Не вдалося завантажити категорії.');
  return data.categories.map(item => text(record(item).strCategory)).filter(Boolean);
}
