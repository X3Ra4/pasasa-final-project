import { useEffect, useState } from 'react';
import { Animated, FlatList, Platform, Pressable, Text, View } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { ShoppingItem } from '@/core/types';
import { useApp } from '@/state/AppContext';
import { useTheme } from '@/ui/theme';
import { Button, Empty, Heading, Page, styles, useReducedMotion } from '@/ui/components';

function ShoppingRow({ item }: { item: ShoppingItem }) {
  const app = useApp(), c = useTheme(), reduced = useReducedMotion();
  const [opacity] = useState(() => new Animated.Value(item.checked ? .5 : 1));
  useEffect(() => { const animation = Animated.timing(opacity, { toValue: item.checked ? .5 : 1, duration: reduced ? 0 : 220, useNativeDriver: Platform.OS !== 'web' }); animation.start(); return () => animation.stop(); }, [item.checked, opacity, reduced]);
  const toggle = () => void app.update(data => ({ ...data, shopping: data.shopping.map(row => row.id === item.id ? { ...row, checked: !row.checked } : row) })).catch(() => undefined);
  return <Animated.View style={{ opacity, backgroundColor: c.card, borderColor: c.line, borderWidth: 1, borderRadius: 17, marginBottom: 10, flexDirection: 'row', alignItems: 'center' }}>
    <Pressable accessibilityRole="checkbox" accessibilityLabel={`${item.name}, ${item.amount}`} accessibilityState={{ checked: item.checked }} aria-checked={item.checked} onPress={toggle} style={{ flex: 1, padding: 17, flexDirection: 'row', alignItems: 'center', gap: 14 }}>
      <Ionicons name={item.checked ? 'checkmark-circle' : 'ellipse-outline'} size={25} color={item.checked ? c.green : c.muted} />
      <View style={{ flex: 1, gap: 4 }}><Text style={{ color: c.ink, fontWeight: '600', textDecorationLine: item.checked ? 'line-through' : 'none' }}>{item.name}</Text>
        <Text style={{ color: c.muted, fontSize: 12 }}>{item.amount || 'За потребою'}{item.source ? ` · ${item.source}` : ''}</Text></View>
    </Pressable><Pressable accessibilityRole="button" accessibilityLabel={`Видалити ${item.name}`} onPress={() => void app.update(data => ({ ...data, shopping: data.shopping.filter(row => row.id !== item.id) })).catch(() => undefined)} style={{ padding: 17 }}><Ionicons name="close-outline" color={c.muted} size={20} /></Pressable>
  </Animated.View>;
}
export default function Shopping() {
  const app = useApp(), c = useTheme();
  const [confirm, setConfirm] = useState(false);
  const checked = app.data.shopping.filter(item => item.checked).length;
  return <Page><FlatList data={app.data.shopping} keyExtractor={item => item.id} renderItem={({ item }) => <ShoppingRow item={item} />}
    contentContainerStyle={{ paddingHorizontal: 22, paddingBottom: 35, flexGrow: 1 }}
    ListHeaderComponent={<View><View style={{ marginHorizontal: -22 }}><Heading eyebrow="УСЕ ДЛЯ ВАШИХ СМАЧНИХ ПЛАНІВ" title="За покупками" subtitle="Додавайте інгредієнти з рецептів або записуйте власні. Список працює офлайн." /></View>
      <View style={{ backgroundColor: c.greenSoft, borderRadius: 20, padding: 20, gap: 12, marginBottom: 20 }}><View style={[styles.row, { justifyContent: 'space-between' }]}><Text style={{ color: c.green, fontWeight: '700' }}>Уже в кошику</Text><Text style={{ color: c.green }}>{checked} / {app.data.shopping.length}</Text></View>
        <View style={{ height: 5, backgroundColor: c.line, borderRadius: 5 }}><View style={{ height: 5, borderRadius: 5, backgroundColor: c.green, width: `${app.data.shopping.length ? checked / app.data.shopping.length * 100 : 0}%` }} /></View></View>
      <Button label="Додати продукт" icon="add" onPress={() => router.push('/shopping/new')} style={{ marginBottom: 22 }} />
      {checked > 0 && <View style={{ gap: 10, marginBottom: 20 }}><Button secondary label={confirm ? 'Підтвердити видалення придбаних' : 'Прибрати придбане'} onPress={() => {
        if (!confirm) setConfirm(true); else void app.update(data => ({ ...data, shopping: data.shopping.filter(row => !row.checked) })).then(() => setConfirm(false)).catch(() => undefined);
      }} />{confirm && <Button secondary label="Скасувати" onPress={() => setConfirm(false)} />}</View>}
    </View>}
    ListEmptyComponent={<Empty title="Список поки порожній" text="Інгредієнти можна додати одним натисканням зі сторінки рецепта. А молоко чи хліб — вручну." icon="basket-outline" />} /></Page>;
}
