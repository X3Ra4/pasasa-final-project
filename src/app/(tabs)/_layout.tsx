import { Redirect, Tabs } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { useApp } from '@/state/AppContext';
import { useTheme } from '@/ui/theme';

export default function TabLayout() {
  const app = useApp(), c = useTheme();
  const insets = useSafeAreaInsets();
  if (!app.data.onboarded) return <Redirect href="/onboarding" />;
  return <Tabs screenOptions={{ headerShown: false, tabBarActiveTintColor: c.accent, tabBarInactiveTintColor: c.muted,
    tabBarStyle: { backgroundColor: c.card, borderTopColor: c.line, height: 64 + insets.bottom, paddingBottom: Math.max(insets.bottom, 8), paddingTop: 5 }, tabBarLabelStyle: { fontSize: 10, fontWeight: '600' } }}>
    <Tabs.Screen name="index" options={{ title: 'Натхнення', tabBarIcon: ({ color, size }) => <Ionicons name="restaurant-outline" color={color} size={size} /> }} />
    <Tabs.Screen name="saved" options={{ title: 'Обране', tabBarIcon: ({ color, size }) => <Ionicons name="heart-outline" color={color} size={size} />, tabBarBadge: Object.keys(app.data.favorites).length || undefined }} />
    <Tabs.Screen name="shopping" options={{ title: 'Покупки', tabBarIcon: ({ color, size }) => <Ionicons name="basket-outline" color={color} size={size} /> }} />
    <Tabs.Screen name="settings" options={{ title: 'Мій Smak', tabBarIcon: ({ color, size }) => <Ionicons name="options-outline" color={color} size={size} /> }} />
  </Tabs>;
}
