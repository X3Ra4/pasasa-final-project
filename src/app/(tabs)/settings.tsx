import { useState } from 'react';
import { Linking, ScrollView, Switch, Text, View } from 'react-native';
import { router } from 'expo-router';
import { useApp } from '@/state/AppContext';
import { useTheme } from '@/ui/theme';
import { Button, Heading, Page, styles } from '@/ui/components';

export default function Settings() {
  const app = useApp(), c = useTheme(), [confirm, setConfirm] = useState(false);
  return <Page><ScrollView contentContainerStyle={{ padding: 24, gap: 22 }}><View style={{ margin: -24, marginBottom: -12 }}><Heading eyebrow="ТРОХИ БІЛЬШЕ ПРО ВАС" title="Мій Smak" subtitle="Затишний простір для ваших кулінарних ідей." /></View>
    <View style={{ padding: 22, borderRadius: 21, backgroundColor: c.card, borderWidth: 1, borderColor: c.line, gap: 18 }}>
      <View style={[styles.row, { justifyContent: 'space-between' }]}><View style={{ flex: 1 }}><Text style={{ color: c.ink, fontWeight: '700', fontSize: 17 }}>Темна тема</Text><Text style={{ color: c.muted, marginTop: 5, fontSize: 12 }}>Для вечірніх кулінарних планів</Text></View><Switch accessibilityLabel="Темна тема" value={app.data.theme === 'dark'} onValueChange={value => void app.update(data => ({ ...data, theme: value ? 'dark' : 'light' })).catch(() => undefined)} trackColor={{ true: c.accent }} /></View>
      <Text style={{ color: c.muted, lineHeight: 22 }}>Обраних рецептів: {Object.keys(app.data.favorites).length}{'\n'}У списку покупок: {app.data.shopping.length}</Text>
    </View>
    <View style={{ gap: 12 }}><Text style={{ color: c.ink, fontSize: 18, fontWeight: '700' }}>Ваші дані залишаються у вас</Text><Text style={{ color: c.muted, lineHeight: 24 }}>Обране, нотатки, покупки та тема зберігаються на цьому пристрої. Акаунт не потрібен. Видалення застосунку або даних браузера може видалити ці записи.</Text></View>
    <View style={{ gap: 12 }}><Text style={{ color: c.ink, fontSize: 18, fontWeight: '700' }}>Рецепти з усього світу</Text><Text style={{ color: c.muted, lineHeight: 24 }}>Джерело рецептів і фото — TheMealDB. Назви, інгредієнти та інструкції залишаються мовою джерела. Для пошуку вводьте англійські слова. Фото кешуються, але офлайн гарантовано доступні саме збережені тексти.</Text>
      <Button label="Про API TheMealDB" secondary icon="open-outline" onPress={() => void Linking.openURL('https://www.themealdb.com/api.php').catch(() => undefined)} /></View>
    <Text style={{ color: c.muted, fontSize: 12, lineHeight: 20 }}>Smak 1.0 · навчальний проєкт React Native + Expo. Рецепти не містять перевірених даних про алергени чи харчову цінність — перевіряйте склад самостійно.</Text>
    <Button label={confirm ? 'Так, видалити всі локальні дані' : 'Скинути дані застосунку'} secondary onPress={() => {
      if (!confirm) setConfirm(true); else void app.reset().then(() => router.replace('/onboarding')).catch(() => undefined);
    }} />{confirm && <><Text style={{ color: c.danger }}>Обране, нотатки й покупки буде видалено. Цю дію неможливо скасувати.</Text><Button secondary label="Залишити мої дані" onPress={() => setConfirm(false)} /></>}
  </ScrollView></Page>;
}
