import { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, Text, TextInput, View } from 'react-native';
import { router } from 'expo-router';
import { addShoppingItem, validateShopping } from '@/core/store';
import { useApp } from '@/state/AppContext';
import { useTheme } from '@/ui/theme';
import { Button, Heading, Page, styles } from '@/ui/components';

export default function NewShoppingItem() {
  const app = useApp(), c = useTheme();
  const [name, setName] = useState(''), [amount, setAmount] = useState(''), [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const save = async () => {
    if (saving) return;
    const error = validateShopping(name, amount);
    if (error) { setError(error); return; }
    setSaving(true); setError('');
    try {
      const id = `manual:${Date.now()}:${Math.random().toString(36).slice(2, 10)}`;
      await app.update(data => addShoppingItem(data, name, amount, id));
      router.replace('/(tabs)/shopping');
    } catch (error) { setError(error instanceof Error ? error.message : 'Не вдалося зберегти.'); }
    finally { setSaving(false); }
  };
  return <Page><KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}><ScrollView keyboardShouldPersistTaps="handled" contentContainerStyle={{ padding: 24, gap: 22 }}>
    <View style={{ margin: -24, marginBottom: -8 }}><Heading eyebrow="ЩО ЩЕ ЗНАДОБИТЬСЯ?" title="Додамо до списку" subtitle="Запишіть продукт і потрібну кількість. Жодна дрібниця не загубиться." /></View>
    <View><Text style={[styles.label, { color: c.ink }]}>Назва продукту *</Text><TextInput accessibilityLabel="Назва продукту" autoFocus value={name} onChangeText={setName} placeholder="Наприклад, молоко" placeholderTextColor={c.muted} maxLength={81} style={[styles.input, { color: c.ink, borderColor: c.line, backgroundColor: c.card }]} /></View>
    <View><Text style={[styles.label, { color: c.ink }]}>Кількість або примітка</Text><TextInput accessibilityLabel="Кількість" value={amount} onChangeText={setAmount} placeholder="1 л, 2 шт. або за смаком" placeholderTextColor={c.muted} maxLength={41} onSubmitEditing={() => void save()} style={[styles.input, { color: c.ink, borderColor: c.line, backgroundColor: c.card }]} /></View>
    {!!error && <Text accessibilityRole="alert" style={{ color: c.danger }}>{error}</Text>}
    <Button label={saving ? 'Зберігаємо…' : 'Зберегти продукт'} icon="add-circle-outline" onPress={() => void save()} disabled={saving} />
    <Button secondary label="Скасувати" onPress={() => router.back()} disabled={saving} />
  </ScrollView></KeyboardAvoidingView></Page>;
}
