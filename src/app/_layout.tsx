import { useState } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { Text, View } from 'react-native';
import { AppProvider, useApp } from '@/state/AppContext';
import { Button, Empty, Loading, OfflineBanner, Page } from '@/ui/components';
import { useTheme } from '@/ui/theme';

function Navigation() {
  const app = useApp(), c = useTheme();
  const [confirm, setConfirm] = useState(false);
  if (!app.ready) return <SafeAreaView style={{ flex: 1, backgroundColor: c.bg }}><Page>
    {app.error ? <><Empty title="Ваші дані важливі" text={app.error} icon="shield-checkmark-outline" action="Повторити читання" onPress={() => void app.reload()} />
      <View style={{ padding: 24, gap: 12 }}><Button secondary label={confirm ? 'Підтвердити видалення локальних даних' : 'Скинути локальні дані'}
        onPress={() => { if (!confirm) setConfirm(true); else void app.reset().catch(() => undefined); }} />
        {confirm && <Button label="Скасувати" secondary onPress={() => setConfirm(false)} />}</View></> : <Loading />}
  </Page></SafeAreaView>;
  return <View style={{ flex: 1, backgroundColor: c.bg }}>
    <StatusBar style={app.data.theme === 'dark' ? 'light' : 'dark'} />
    <SafeAreaView edges={['top']} style={{ backgroundColor: c.bg }}><OfflineBanner />
      {!!app.error && <View style={{ padding: 14, gap: 10, backgroundColor: c.soft }}><Text accessibilityRole="alert" style={{ color: c.danger }}>{app.error}</Text><Button label="Закрити повідомлення" secondary onPress={app.dismissError} /></View>}
    </SafeAreaView>
    <Stack screenOptions={{ headerStyle: { backgroundColor: c.bg }, headerTintColor: c.ink, headerShadowVisible: false, contentStyle: { backgroundColor: c.bg }, animation: 'slide_from_right' }}>
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="meal/[id]" options={{ title: 'Рецепт', presentation: 'card' }} />
      <Stack.Screen name="shopping/new" options={{ title: 'Додати продукт', presentation: 'modal' }} />
      <Stack.Screen name="onboarding" options={{ headerShown: false, gestureEnabled: false }} />
    </Stack>
  </View>;
}
export default function RootLayout() { return <SafeAreaProvider><AppProvider><Navigation /></AppProvider></SafeAreaProvider>; }
