import { useCallback, useRef, useState } from 'react';
import { FlatList, Linking, Text, TextInput, View } from 'react-native';
import { router, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { getMeal } from '@/core/api';
import { addIngredients } from '@/core/store';
import { Meal } from '@/core/types';
import { useApp } from '@/state/AppContext';
import { useRequest } from '@/hooks/useRequest';
import { Button, Empty, Entrance, ErrorState, Heading, Loading, Page, RecipeImage, styles } from '@/ui/components';
import { useTheme } from '@/ui/theme';

export default function MealDetail() {
  const params = useLocalSearchParams<{ id: string }>();
  const id = typeof params.id === 'string' ? params.id : '';
  const app = useApp(), c = useTheme(), saved = app.data.favorites[id];
  const inMemory = useRef<Meal | null>(null);
  const loader = useCallback(async (signal: AbortSignal) => {
    if (saved) { inMemory.current = saved; return saved; }
    if (inMemory.current?.id === id) return inMemory.current;
    const meal = await getMeal(id, signal);
    if (!signal.aborted) inMemory.current = meal;
    return meal;
  }, [id, saved]);
  const request = useRequest<Meal | null>(loader, null);
  const [draft, setDraft] = useState({ id, value: app.data.notes[id] || '' });
  const note = draft.id === id ? draft.value : app.data.notes[id] || '';
  const [message, setMessage] = useState('');

  const meal = request.data;
  if (request.loading) return <Page><Loading /></Page>;
  if (request.error) return <Page><ErrorState message={request.error} retry={request.retry} /></Page>;
  if (!meal) return <Page><Empty title="Рецепт не знайдено" text="Можливо, його видалили з каталогу. Поверніться до пошуку." action="До рецептів" onPress={() => router.replace('/')} /></Page>;
  const toggle = async () => {
    await app.update(data => {
      const favorites = { ...data.favorites };
      if (favorites[id]) delete favorites[id]; else favorites[id] = meal;
      return { ...data, favorites };
    });
  };
  return <Page><FlatList data={meal.ingredients} keyExtractor={(_, index) => `${id}:${index}`} contentContainerStyle={{ paddingBottom: 36 }}
    ListHeaderComponent={<Entrance><RecipeImage uri={meal.image} height={280} /><Heading eyebrow={[meal.category, meal.area].filter(Boolean).join(' · ')} title={meal.name} subtitle="Рецепт та інгредієнти наведено мовою TheMealDB." />
      <View style={{ paddingHorizontal: 24, gap: 12 }}><Button testID="save-recipe" label={saved ? 'Прибрати з обраного' : 'Зберегти рецепт'} icon={saved ? 'heart' : 'heart-outline'} secondary={!!saved} disabled={app.busy} onPress={() => void toggle().catch(() => undefined)} />
        <View style={[styles.row, { marginTop: 7 }]}><Ionicons name="cloud-done-outline" color={c.green} size={17} /><Text style={{ flex: 1, fontSize: 12, color: c.muted }}>{saved ? 'Текст цього рецепта збережено для офлайн-доступу.' : 'Збережіть рецепт, щоб мати його під рукою без інтернету.'}</Text></View>
        <Text accessibilityRole="header" style={{ fontSize: 22, fontWeight: '700', color: c.ink, marginTop: 19, marginBottom: 5 }}>Інгредієнти <Text style={{ color: c.muted, fontWeight: '400' }}>· {meal.ingredients.length}</Text></Text>
      </View></Entrance>}
    renderItem={({ item }) => <View style={{ marginHorizontal: 24, paddingVertical: 13, borderBottomWidth: 1, borderBottomColor: c.line, flexDirection: 'row', gap: 16 }}><Text style={{ flex: 1, color: c.ink, fontSize: 14 }}>{item.name}</Text><Text style={{ color: c.muted, maxWidth: '45%', fontSize: 13, textAlign: 'right' }}>{item.amount || 'За смаком'}</Text></View>}
    ListEmptyComponent={<Empty title="Немає інгредієнтів" text="Спробуйте оновити рецепт." />}
    ListFooterComponent={<View style={{ padding: 24, gap: 22 }}>
      <Button label="До списку покупок" icon="basket-outline" disabled={app.busy} onPress={() => void app.update(data => addIngredients(data, meal)).then(() => setMessage('Інгредієнти додано до покупок. Повторів не створено.')).catch(() => undefined)} />
      {!!message && <Text accessibilityLiveRegion="polite" style={{ color: c.green, fontSize: 13 }}>{message}</Text>}
      <Text accessibilityRole="header" style={{ color: c.ink, fontSize: 22, fontWeight: '700' }}>Готуємо разом</Text><Text style={{ color: c.ink, fontSize: 15, lineHeight: 27 }}>{meal.instructions}</Text>
      {!!meal.source && <Button secondary label="Джерело рецепта" icon="open-outline" onPress={() => void Linking.openURL(meal.source).catch(() => setMessage('Не вдалося відкрити посилання.'))} />}
      <View style={{ padding: 20, backgroundColor: c.greenSoft, borderRadius: 21, gap: 12 }}><Text style={{ color: c.ink, fontSize: 18, fontWeight: '700' }}>Маленька нотатка для себе</Text><Text style={{ color: c.muted, fontSize: 12 }}>Менше солі? Більше спецій? Запишіть свою ідею.</Text>
        <TextInput accessibilityLabel="Нотатка до рецепта" multiline value={note} onChangeText={value => setDraft({ id, value })} maxLength={1000} placeholder="Наступного разу спробую…" placeholderTextColor={c.muted} style={[styles.input, { color: c.ink, borderColor: c.line, backgroundColor: c.card, minHeight: 100, textAlignVertical: 'top' }]} />
        <Text style={{ color: c.muted, fontSize: 11 }}>{note.length}/1000</Text><Button secondary label="Зберегти нотатку" disabled={app.busy} onPress={() => {
          if (note.length > 1000) { setMessage('Нотатка — не більше 1000 символів.'); return; }
          void app.update(data => ({ ...data, notes: { ...data.notes, [id]: note.trim() } })).then(() => setMessage('Нотатку збережено на пристрої.')).catch(() => undefined);
        }} /></View>
    </View>} /></Page>;
}
