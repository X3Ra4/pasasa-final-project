import { Ionicons } from '@expo/vector-icons';
import { Redirect, router } from 'expo-router';
import { ScrollView, Text, View } from 'react-native';
import { useApp } from '@/state/AppContext';
import { useTheme } from '@/ui/theme';
import { Button, Entrance, Page, styles } from '@/ui/components';

export default function Onboarding() {
  const app = useApp(), c = useTheme();
  if (app.data.onboarded) return <Redirect href="/" />;
  return <Page><ScrollView contentContainerStyle={{ padding: 30, flexGrow: 1, justifyContent: 'center', maxWidth: 620, width: '100%', alignSelf: 'center' }}><Entrance>
    <Text style={{ color: c.accent, fontSize: 42, letterSpacing: -2, fontWeight: '800', marginBottom: 32 }}>smak<Text style={{ color: c.green }}>.</Text></Text>
    <View style={{ alignItems: 'center', padding: 36, backgroundColor: c.greenSoft, borderRadius: 100, alignSelf: 'center', marginBottom: 36 }}><Ionicons name="restaurant-outline" size={74} color={c.green} /></View>
    <Text style={[styles.eyebrow, { color: c.accent, marginBottom: 15 }]}>ВАША НОВА КУЛІНАРНА ЗВИЧКА</Text>
    <Text accessibilityRole="header" style={{ color: c.ink, fontSize: 39, lineHeight: 47, letterSpacing: -1, fontWeight: '800' }}>Трохи натхнення.{ '\n' }Багато смаку.</Text>
    <Text style={{ color: c.muted, fontSize: 15, lineHeight: 25, marginTop: 18, marginBottom: 26 }}>Шукайте рецепти з усього світу, зберігайте улюблене та збирайте список покупок одним натисканням.</Text>
    <View style={{ gap: 14, marginBottom: 32 }}><View style={styles.row}><Ionicons name="search-outline" size={20} color={c.accent} /><Text style={{ color: c.ink, flex: 1 }}>Реальні рецепти, пошук англійською</Text></View><View style={styles.row}><Ionicons name="heart-outline" size={20} color={c.accent} /><Text style={{ color: c.ink, flex: 1 }}>Улюблені тексти доступні офлайн</Text></View><View style={styles.row}><Ionicons name="basket-outline" size={20} color={c.accent} /><Text style={{ color: c.ink, flex: 1 }}>Покупки та нотатки завжди поруч</Text></View></View>
    <Button label="Почати готувати" icon="arrow-forward" disabled={app.busy} onPress={() => void app.update(data => ({ ...data, onboarded: true })).then(() => router.replace('/')).catch(() => undefined)} />
    <Text style={{ color: c.muted, fontSize: 11, textAlign: 'center', marginTop: 18 }}>Без реєстрації. Ваші плани зберігаються на пристрої.</Text>
  </Entrance></ScrollView></Page>;
}
