import { AppData, emptyData, Meal, ShoppingItem } from './types';

export const STORAGE_KEY = '@smak/state:v1';
type Storage = { getItem(key: string): Promise<string | null>; setItem(key: string, value: string): Promise<void> };
const object = (value: unknown): value is Record<string, unknown> => !!value && typeof value === 'object' && !Array.isArray(value);
const string = (value: unknown): value is string => typeof value === 'string';
const id = (value: unknown): value is string => string(value) && /^\d{1,12}$/.test(value);
function validMeal(value: unknown): value is Meal {
  if (!object(value) || !id(value.id) || !string(value.name) || !value.name || !string(value.image) ||
    !string(value.instructions) || !string(value.source) || !string(value.video) || !Array.isArray(value.ingredients)) return false;
  return (!value.image || value.image.startsWith('https://')) && (!value.source || value.source.startsWith('https://')) &&
    (!value.video || value.video.startsWith('https://')) && value.ingredients.every(item => object(item) && string(item.name) && string(item.amount));
}
export function parseStored(raw: string | null): AppData {
  if (raw === null) return emptyData();
  let value: unknown;
  try { value = JSON.parse(raw); } catch { throw new Error('Збережені дані пошкоджено.'); }
  if (!object(value) || value.version !== 1 || !['light', 'dark'].includes(String(value.theme)) ||
      typeof value.onboarded !== 'boolean' || !object(value.favorites) || !object(value.notes) || !Array.isArray(value.shopping)) {
    throw new Error('Невідома версія або формат збережених даних.');
  }
  if (!Object.entries(value.favorites).every(([key, meal]) => validMeal(meal) && meal.id === key) ||
      !Object.entries(value.notes).every(([key, note]) => id(key) && string(note) && note.length <= 1000) ||
      !value.shopping.every(row => object(row) && string(row.id) && string(row.name) && !!row.name &&
        string(row.amount) && typeof row.checked === 'boolean' &&
        (row.source === undefined || string(row.source)) && (row.sourceId === undefined || string(row.sourceId)))) {
    throw new Error('Збережені дані мають некоректні поля.');
  }
  if (new Set(value.shopping.map(row => row.id)).size !== value.shopping.length) throw new Error('Некоректні повтори у списку покупок.');
  return value as AppData;
}
export function validateShopping(name: string, amount: string): string | null {
  if (!name.trim()) return 'Введіть назву продукту.';
  if (name.trim().length > 80) return 'Назва — не більше 80 символів.';
  if (amount.trim().length > 40) return 'Кількість — не більше 40 символів.';
  return null;
}
export function addShoppingItem(data: AppData, name: string, amount: string, rowId: string): AppData {
  const error = validateShopping(name, amount);
  if (error) throw new Error(error);
  if (data.shopping.some(row => row.id === rowId)) throw new Error('Такий запис уже існує.');
  return { ...data, shopping: [...data.shopping, { id: rowId, name: name.trim(), amount: amount.trim(), checked: false }] };
}
export function addIngredients(data: AppData, meal: Meal): AppData {
  const rows: ShoppingItem[] = meal.ingredients.map((ingredient, index) => ({
    id: `meal:${meal.id}:${index}`, ...ingredient, checked: false, source: meal.name, sourceId: meal.id,
  }));
  return { ...data, shopping: [...data.shopping, ...rows.filter(row => !data.shopping.some(old => old.id === row.id))] };
}
export function createStore(storage: Storage) {
  let snapshot = { data: emptyData(), ready: false, busy: false, error: '' };
  const listeners = new Set<() => void>();
  let queue: Promise<unknown> = Promise.resolve();
  let loading: Promise<void> | null = null;
  const publish = (next: typeof snapshot) => { snapshot = next; listeners.forEach(listener => listener()); };
  const enqueue = (operation: () => Promise<void>): Promise<void> => {
    const next = queue.catch(() => undefined).then(operation);
    queue = next;
    return next;
  };
  const persist = async (data: AppData) => {
    publish({ ...snapshot, busy: true, error: '' });
    try {
      const validated = parseStored(JSON.stringify(data));
      await storage.setItem(STORAGE_KEY, JSON.stringify(validated));
      publish({ data: validated, ready: true, busy: false, error: '' });
    } catch {
      publish({ ...snapshot, busy: false, error: 'Не вдалося зберегти зміни. Попередні дані залишилися без змін.' });
      throw new Error(snapshot.error);
    }
  };
  return {
    getSnapshot: () => snapshot,
    subscribe: (listener: () => void) => { listeners.add(listener); return () => { listeners.delete(listener); }; },
    load: () => {
      if (loading) return loading;
      loading = enqueue(async () => {
        publish({ ...snapshot, busy: true, error: '' });
        try { publish({ data: parseStored(await storage.getItem(STORAGE_KEY)), ready: true, busy: false, error: '' }); }
        catch { publish({ ...snapshot, ready: false, busy: false, error: 'Не вдалося прочитати ваші дані. Повторіть спробу або підтвердьте скидання.' }); }
      }).finally(() => { loading = null; });
      return loading;
    },
    update: (transform: (data: AppData) => AppData) => enqueue(async () => {
      if (!snapshot.ready) throw new Error('Спочатку потрібно відновити доступ до сховища.');
      await persist(transform(parseStored(JSON.stringify(snapshot.data))));
    }),
    reset: () => enqueue(() => persist(emptyData())),
    dismissError: () => publish({ ...snapshot, error: '' }),
  };
}
