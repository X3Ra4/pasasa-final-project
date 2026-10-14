import { useState } from 'react';
import { FlatList, View } from 'react-native';
import { router } from 'expo-router';
import { useApp } from '@/state/AppContext';
import { Empty, Heading, MealCard, Page, useLayout } from '@/ui/components';

export default function Saved() {
  const app = useApp(), { columns } = useLayout();
  const [refreshing, setRefreshing] = useState(false);
  const refresh = async () => { setRefreshing(true); await app.reload(); setRefreshing(false); };
  return <Page><FlatList key={columns} numColumns={columns} data={Object.values(app.data.favorites)} keyExtractor={item => item.id}
    onRefresh={() => void refresh()} refreshing={refreshing} columnWrapperStyle={columns > 1 ? { gap: 16 } : undefined}
    contentContainerStyle={{ paddingHorizontal: 22, paddingBottom: 30, flexGrow: 1 }}
    ListHeaderComponent={<View style={{ marginHorizontal: -22 }}><Heading eyebrow="ВАША ОСОБИСТА КУЛІНАРНА КНИГА" title="Збережено з любов’ю" subtitle="Улюблені рецепти завжди поруч. Тексти та інгредієнти доступні навіть без інтернету." /></View>}
    renderItem={({ item }) => <View style={{ flex: 1, maxWidth: `${100 / columns}%` }}><MealCard meal={item} /></View>}
    ListEmptyComponent={<Empty icon="heart-outline" title="Тут житимуть ваші улюблені" text="Відкрийте рецепт і натисніть «Зберегти рецепт». Ми збережемо всі інгредієнти та інструкції." action="Знайти щось смачне" onPress={() => router.navigate('/')} />} /></Page>;
}
