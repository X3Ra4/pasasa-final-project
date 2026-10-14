import { describe, expect, it, vi } from 'vitest';
import { normalizeMeal, normalizeSummaries, searchMeals, getMeal, getCategories } from './api';
import { addIngredients, addShoppingItem, validateShopping, parseStored, createStore } from './store';
import { emptyData, Meal } from './types';

const raw = { idMeal: '52772', strMeal: 'Teriyaki Chicken', strMealThumb: 'https://www.themealdb.com/test.jpg',
  strCategory: 'Chicken', strArea: 'Japanese', strInstructions: 'Cook carefully.', strIngredient1: ' Chicken ',
  strMeasure1: ' 500 g ', strIngredient2: '', strMeasure2: '', strSource: 'https://example.com/recipe' };
const meal: Meal = { id: '52772', name: 'Teriyaki Chicken', image: 'https://www.themealdb.com/test.jpg',
  category: 'Chicken', area: 'Japanese', instructions: 'Cook carefully.',
  ingredients: [{ name: 'Chicken', amount: '500 g' }], source: 'https://example.com/recipe', video: '' };
const response = (data: unknown, status = 200) => Promise.resolve(new Response(JSON.stringify(data), { status }));

describe('API boundary', () => {
  it('normalizes full recipe without blank ingredients or fake nutrition', () => expect(normalizeMeal(raw)).toEqual(meal));
  it('handles null search results', () => expect(normalizeSummaries(null)).toEqual([]));
  it('rejects malformed recipe details', () => expect(() => normalizeMeal({ idMeal: '2' })).toThrow());
  it('ignores unsafe image and source URLs', () => {
    const result = normalizeMeal({ ...raw, strMealThumb: 'javascript:bad', strSource: 'file:///secret' });
    expect(result.image).toBe(''); expect(result.source).toBe('');
  });
  it('sends encoded search to the actual server endpoint', async () => {
    const fetcher = vi.fn().mockImplementation(() => response({ meals: [raw] }));
    const result = await searchMeals({ query: 'fish & chips' }, undefined, fetcher);
    expect(fetcher.mock.calls[0][0]).toContain('search.php?s=fish%20%26%20chips');
    expect(result[0].id).toBe('52772');
  });
  it('sends category filter to server', async () => {
    const fetcher = vi.fn().mockImplementation(() => response({ meals: null }));
    expect(await searchMeals({ category: 'Seafood' }, undefined, fetcher)).toEqual([]);
    expect(fetcher.mock.calls[0][0]).toContain('filter.php?c=Seafood');
  });
  it('returns missing detail as null', async () => expect(await getMeal('123', undefined, () => response({ meals: null }))).toBeNull());
  it('rejects HTTP errors', async () => expect(searchMeals({}, undefined, () => response({}, 503))).rejects.toThrow());
  it('rejects invalid API shapes instead of false empty success', async () => expect(searchMeals({}, undefined, () => response({ invalid: [] }))).rejects.toThrow());
  it('rejects invalid detail ID before network', async () => {
    const fetcher = vi.fn(); await expect(getMeal('../etc', undefined, fetcher)).rejects.toThrow(); expect(fetcher).not.toHaveBeenCalled();
  });
  it('loads categories', async () => expect(await getCategories(undefined, () => response({ categories: [{ strCategory: 'Seafood' }] }))).toEqual(['Seafood']));
});

describe('local data', () => {
  it.each([{}, [], 12])('rejects malformed optional recipe metadata %j', invalid => {
    for (const field of ['category', 'area']) {
      expect(() => parseStored(JSON.stringify({ ...emptyData(), favorites: { [meal.id]: { ...meal, [field]: invalid } } }))).toThrow();
    }
  });
  it('provides clean first-run defaults', () => expect(parseStored(null)).toEqual(emptyData()));
  it('restores favorites, theme and notes', () => {
    const data = { ...emptyData(), theme: 'dark', favorites: { [meal.id]: meal }, notes: { [meal.id]: 'Less salt' } };
    expect(parseStored(JSON.stringify(data))).toEqual(data);
  });
  it('rejects corrupt data without pretending it is empty', () => expect(() => parseStored('{broken')).toThrow());
  it('rejects unsupported versions', () => expect(() => parseStored('{"version":99}')).toThrow());
  it('rejects invalid stored favorite shape', () => expect(() => parseStored(JSON.stringify({ ...emptyData(), favorites: { '1': {} } }))).toThrow());
  it('validates empty/long shopping names and amounts', () => {
    expect(validateShopping(' ', '1')).not.toBeNull(); expect(validateShopping('x'.repeat(81), '1')).not.toBeNull();
    expect(validateShopping('Milk', 'x'.repeat(41))).not.toBeNull(); expect(validateShopping('Milk', '1 l')).toBeNull();
  });
  it('imports ingredients once and preserves checked state', () => {
    let data = addIngredients(emptyData(), meal);
    data.shopping[0].checked = true;
    data = addIngredients(data, meal);
    expect(data.shopping).toHaveLength(1); expect(data.shopping[0].checked).toBe(true);
  });
  it('allows ingredients from distinct recipes without merging quantities', () => {
    const data = addIngredients(addIngredients(emptyData(), meal), { ...meal, id: '2' });
    expect(data.shopping).toHaveLength(2);
  });
  it('trims manual shopping rows', () => expect(addShoppingItem(emptyData(), '  Milk ', ' 1 l ', 'manual:1').shopping[0]).toMatchObject({ name: 'Milk', amount: '1 l', checked: false }));
});

describe('transactional storage', () => {
  it('persists and reloads the complete state', async () => {
    let disk: string | null = null;
    const storage = { getItem: async () => disk, setItem: async (_: string, value: string) => { disk = value; } };
    const store = createStore(storage); await store.load();
    await store.update(data => ({ ...data, theme: 'dark', favorites: { [meal.id]: meal } }));
    const restarted = createStore(storage); await restarted.load(); expect(restarted.getSnapshot().data.theme).toBe('dark');
    expect(restarted.getSnapshot().data.favorites[meal.id].instructions).toBe('Cook carefully.');
  });
  it('does not publish unsaved data when a write fails', async () => {
    const store = createStore({ getItem: async () => null, setItem: async () => { throw new Error('full'); } });
    await store.load(); await expect(store.update(data => ({ ...data, theme: 'dark' }))).rejects.toThrow();
    expect(store.getSnapshot().data.theme).toBe('light'); expect(store.getSnapshot().error).toBeTruthy();
  });
  it('serializes rapid changes without losing either', async () => {
    const writes: string[] = [];
    const store = createStore({ getItem: async () => null, setItem: async (_, value) => { writes.push(value); } });
    await store.load();
    await Promise.all([store.update(data => addShoppingItem(data, 'Milk', '', 'a')), store.update(data => addShoppingItem(data, 'Bread', '', 'b'))]);
    expect(store.getSnapshot().data.shopping).toHaveLength(2); expect(JSON.parse(writes[1]).shopping).toHaveLength(2);
  });
  it('blocks writes after a failed read until explicit reset', async () => {
    const write = vi.fn().mockResolvedValue(undefined);
    const store = createStore({ getItem: async () => '{bad', setItem: write });
    await store.load(); await expect(store.update(data => data)).rejects.toThrow(); expect(write).not.toHaveBeenCalled();
    await store.reset(); expect(store.getSnapshot().ready).toBe(true); expect(write).toHaveBeenCalledOnce();
  });
});
