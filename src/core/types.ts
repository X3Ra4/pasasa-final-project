export type MealSummary = { id: string; name: string; image: string; category?: string; area?: string };
export type Ingredient = { name: string; amount: string };
export type Meal = MealSummary & { instructions: string; ingredients: Ingredient[]; source: string; video: string };
export type ShoppingItem = { id: string; name: string; amount: string; checked: boolean; source?: string; sourceId?: string };
export type AppData = {
  version: 1;
  theme: 'light' | 'dark';
  onboarded: boolean;
  favorites: Record<string, Meal>;
  notes: Record<string, string>;
  shopping: ShoppingItem[];
};
export const emptyData = (): AppData => ({ version: 1, theme: 'light', onboarded: false, favorites: {}, notes: {}, shopping: [] });
