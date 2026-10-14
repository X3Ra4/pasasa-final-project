import { useCallback, useState } from 'react';
import { FlatList, Pressable, Text, TextInput, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { getCategories, searchMeals } from '@/core/api';
import { MealSummary } from '@/core/types';
import { useRequest } from '@/hooks/useRequest';
import { Button, Empty, ErrorState, Heading, Loading, MealCard, Page, RecipeImage, styles, useLayout } from '@/ui/components';
import { useTheme } from '@/ui/theme';

const labels: Record<string, string> = { Chicken: 'Курка', Vegetarian: 'Овочі', Seafood: 'Морепродукти', Dessert: 'Десерти', Pasta: 'Паста', Vegan: 'Веганські', Beef: 'Яловичина', Breakfast: 'Сніданки', Starter: 'Закуски', Side: 'Гарніри', Miscellaneous: 'Різне', Pork: 'Свинина', Lamb: 'Баранина', Goat: 'Козлятина' };
export default function Discover() {
  const c = useTheme(), { columns } = useLayout();
  const [input, setInput] = useState('');
  const [filter, setFilter] = useState<{ query?: string; category?: string }>({ query: 'chicken' });
  const loader = useCallback((signal: AbortSignal) => searchMeals(filter, signal), [filter]);
  const request = useRequest<MealSummary[]>(loader, []);
  const categories = useRequest(useCallback((signal: AbortSignal) => getCategories(signal), []), [] as string[]);
  const search = () => { setFilter({ query: input.trim() }); };
  const first = request.data[0];
  return <Page><FlatList key={columns} numColumns={columns} data={request.loading || request.error ? [] : request.data}
    keyExtractor={item => item.id} refreshing={request.refreshing} onRefresh={request.refresh}
    contentContainerStyle={{ paddingHorizontal: 22, paddingBottom: 25, flexGrow: 1 }}
    columnWrapperStyle={columns > 1 ? { gap: 16 } : undefined}
    renderItem={({ item }) => <View style={{ flex: 1, maxWidth: `${100 / columns}%` }}><MealCard meal={item} /></View>}
    ListHeaderComponent={<View>
      <View style={[styles.row, { marginTop: 22, justifyContent: 'space-between' }]}><Text style={{ fontSize: 29, fontWeight: '800', letterSpacing: -1, color: c.accent }}>smak<Text style={{ color: c.green }}>.</Text></Text><View style={{ backgroundColor: c.greenSoft, padding: 10, borderRadius: 30 }}><Ionicons name="leaf-outline" size={20} color={c.green} /></View></View>
      <View style={{ marginHorizontal: -24 }}><Heading eyebrow="МАЛЕНЬКІ РАДОЩІ ЩОДНЯ" title="Що приготуємо?" subtitle="Знайдіть свій наступний улюблений рецепт." /></View>
      <View style={[styles.row, { backgroundColor: c.card, borderColor: c.line, borderWidth: 1, paddingLeft: 14, borderRadius: 16 }]}><Ionicons name="search-outline" size={20} color={c.muted} />
        <TextInput accessibilityLabel="Пошук рецептів" value={input} onChangeText={setInput} onSubmitEditing={search} placeholder="Chicken, pasta, soup…" placeholderTextColor={c.muted} maxLength={80} returnKeyType="search" style={{ flex: 1, minWidth: 0, padding: 14, color: c.ink, fontSize: 14 }} />
        <Pressable accessibilityRole="button" accessibilityLabel="Шукати" onPress={search} style={{ padding: 14 }}><Ionicons name="arrow-forward" size={22} color={c.accent} /></Pressable></View>
      <Text style={{ color: c.muted, fontSize: 11, marginTop: 9, marginBottom: 20 }}>Пошук англійською · рецепти з TheMealDB</Text>
      {!filter.category && !input && !request.loading && !request.error && first && <Pressable accessibilityRole="button" accessibilityLabel="Спробуйте сьогодні" onPress={() => router.push({ pathname: '/meal/[id]', params: { id: first.id } })} style={{ backgroundColor: c.greenSoft, borderRadius: 22, padding: 19, flexDirection: 'row', alignItems: 'center', gap: 14, marginBottom: 25, overflow: 'hidden' }}>
        <View style={{ flex: 1, gap: 10 }}><Text style={[styles.eyebrow, { color: c.green }]}>ТРОХИ НАТХНЕННЯ</Text><Text style={{ color: c.ink, fontSize: 22, fontWeight: '700', lineHeight: 28 }}>Смачно — це{ '\n' }може бути просто.</Text><Text style={{ color: c.green, fontSize: 12, fontWeight: '600' }}>Спробуйте сьогодні →</Text></View><View style={{ width: 100, borderRadius: 50, overflow: 'hidden' }}><RecipeImage uri={first.image} height={100} /></View>
      </Pressable>}
      <FlatList horizontal showsHorizontalScrollIndicator={false} data={['Усі', ...categories.data]} keyExtractor={item => item}
        ListEmptyComponent={<Text style={{ color: c.muted }}>Категорії завантажуються</Text>} contentContainerStyle={{ gap: 8, paddingBottom: 22 }}
        renderItem={({ item }) => { const selected = item === 'Усі' ? !filter.category : filter.category === item;
          return <Pressable accessibilityRole="button" accessibilityState={{ selected }} onPress={() => { setInput(''); setFilter(item === 'Усі' ? { query: 'chicken' } : { category: item }); }} style={{ backgroundColor: selected ? c.accent : c.card, borderColor: selected ? c.accent : c.line, borderWidth: 1, borderRadius: 25, paddingVertical: 10, paddingHorizontal: 17 }}><Text style={{ color: selected ? c.white : c.muted, fontSize: 12, fontWeight: '600' }}>{labels[item] || item}</Text></Pressable>; }} />
      {!!categories.error && <Button secondary label="Повторити завантаження категорій" onPress={categories.retry} style={{ marginBottom: 15 }} />}
      <View style={[styles.row, { justifyContent: 'space-between', marginBottom: 17 }]}><Text accessibilityRole="header" style={{ color: c.ink, fontSize: 20, fontWeight: '700' }}>{filter.category ? labels[filter.category] || filter.category : filter.query === 'chicken' ? 'Ідеї з куркою' : 'Результати пошуку'}</Text><Text style={{ color: c.muted, fontSize: 12 }}>{request.loading ? '…' : request.error ? '' : `${request.data.length} рецептів`}</Text></View>
    </View>}
    ListEmptyComponent={request.loading ? <Loading /> : request.error ? <ErrorState message={request.error} retry={request.retry} /> : <Empty title="Ще не знайшли ваш рецепт" text="Спробуйте іншу англійську назву, наприклад pasta, або оберіть категорію." />}
    ListFooterComponent={!request.loading && !request.error && request.data.length ? <Text style={{ textAlign: 'center', color: c.muted, fontSize: 11, marginVertical: 10 }}>Рецепти та фото: TheMealDB · готуйте із задоволенням</Text> : null} />
  </Page>;
}
