import { PropsWithChildren, useEffect, useState } from 'react';
import { AccessibilityInfo, Animated, Platform, Pressable, StyleProp, StyleSheet, Text, View, ViewStyle, useWindowDimensions } from 'react-native';
import { Image } from 'expo-image';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { useNetworkState } from 'expo-network';
import { MealSummary } from '@/core/types';
import { useApp } from '@/state/AppContext';
import { useTheme } from './theme';

const native = Platform.OS !== 'web';
export function useReducedMotion() {
  const [reduced, setReduced] = useState(false);
  useEffect(() => {
    let live = true;
    AccessibilityInfo.isReduceMotionEnabled().then(value => { if (live) setReduced(value); });
    const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', setReduced);
    return () => { live = false; subscription.remove(); };
  }, []);
  return reduced;
}
export function useLayout() {
  const { width } = useWindowDimensions();
  const contentWidth = Math.min(width, 1080);
  return { width: contentWidth, columns: contentWidth >= 800 ? 3 : contentWidth >= 580 ? 2 : 1 };
}
export function Page({ children }: PropsWithChildren) {
  const c = useTheme();
  return <View style={{ flex: 1, backgroundColor: c.bg }}><View style={{ width: '100%', maxWidth: 1080, alignSelf: 'center', flex: 1 }}>{children}</View></View>;
}
export function Heading({ eyebrow, title, subtitle }: { eyebrow?: string; title: string; subtitle?: string }) {
  const c = useTheme();
  return <View style={styles.heading}>{eyebrow && <Text style={[styles.eyebrow, { color: c.accent }]}>{eyebrow}</Text>}
    <Text accessibilityRole="header" style={[styles.title, { color: c.ink }]}>{title}</Text>
    {subtitle && <Text style={[styles.subtitle, { color: c.muted }]}>{subtitle}</Text>}</View>;
}
export function Button({ label, onPress, icon, secondary = false, disabled = false, style, testID }: {
  label: string; onPress: () => void; icon?: keyof typeof Ionicons.glyphMap; secondary?: boolean; disabled?: boolean; style?: StyleProp<ViewStyle>; testID?: string;
}) {
  const c = useTheme(), [scale] = useState(() => new Animated.Value(1)), reduced = useReducedMotion();
  const animate = (toValue: number) => {
    if (reduced) return;
    Animated.spring(scale, { toValue, useNativeDriver: native, speed: 35, bounciness: 3 }).start();
  };
  return <Animated.View style={[{ transform: [{ scale }], opacity: disabled ? .5 : 1 }, style]}>
    <Pressable testID={testID} accessibilityRole="button" accessibilityLabel={label} accessibilityState={{ disabled }} disabled={disabled}
      onPressIn={() => animate(.96)} onPressOut={() => animate(1)} onPress={onPress}
      style={[styles.button, { backgroundColor: secondary ? c.soft : c.accent }]}>
      {icon && <Ionicons name={icon} size={19} color={secondary ? c.accent : c.white} />}
      <Text style={{ fontSize: 14, fontWeight: '700', color: secondary ? c.accent : c.white }}>{label}</Text>
    </Pressable></Animated.View>;
}
export function Entrance({ children }: PropsWithChildren) {
  const [progress] = useState(() => new Animated.Value(0)), reduced = useReducedMotion();
  useEffect(() => {
    if (reduced) { progress.setValue(1); return; }
    const animation = Animated.timing(progress, { toValue: 1, duration: 350, useNativeDriver: native });
    animation.start(); return () => animation.stop();
  }, [progress, reduced]);
  return <Animated.View style={{ opacity: progress, transform: [{ translateY: progress.interpolate({ inputRange: [0, 1], outputRange: [12, 0] }) }] }}>{children}</Animated.View>;
}
export function Loading() {
  const c = useTheme(), [opacity] = useState(() => new Animated.Value(.4)), reduced = useReducedMotion();
  useEffect(() => {
    if (reduced) { opacity.setValue(.7); return; }
    const animation = Animated.loop(Animated.sequence([
      Animated.timing(opacity, { toValue: 1, duration: 750, useNativeDriver: native }),
      Animated.timing(opacity, { toValue: .4, duration: 750, useNativeDriver: native }),
    ])); animation.start(); return () => animation.stop();
  }, [opacity, reduced]);
  return <View accessibilityLabel="Завантаження рецептів" style={{ padding: 24, gap: 18 }}>
    <Text style={{ color: c.muted }}>Шукаємо щось смачне…</Text>
    <Animated.View style={{ opacity, gap: 12 }}><View style={{ height: 190, borderRadius: 22, backgroundColor: c.line }} />
      <View style={{ height: 18, width: '75%', borderRadius: 5, backgroundColor: c.line }} />
      <View style={{ height: 14, width: '45%', borderRadius: 5, backgroundColor: c.line }} /></Animated.View></View>;
}
export function Empty({ title, text, icon = 'leaf-outline', action, onPress }: {
  title: string; text: string; icon?: keyof typeof Ionicons.glyphMap; action?: string; onPress?: () => void;
}) {
  const c = useTheme();
  return <View style={{ padding: 30, alignItems: 'center', gap: 13 }}><View style={{ padding: 19, borderRadius: 28, backgroundColor: c.soft }}><Ionicons name={icon} size={30} color={c.accent} /></View>
    <Text style={{ color: c.ink, fontSize: 21, fontWeight: '700', textAlign: 'center' }}>{title}</Text>
    <Text style={{ color: c.muted, textAlign: 'center', lineHeight: 23, maxWidth: 390 }}>{text}</Text>
    {action && onPress && <Button label={action} onPress={onPress} secondary />}</View>;
}
export function ErrorState({ message, retry }: { message: string; retry: () => void }) {
  return <Empty title="Не вдалося завантажити" text={message} icon="cloud-offline-outline" action="Спробувати ще раз" onPress={retry} />;
}
export function OfflineBanner() {
  const network = useNetworkState(), c = useTheme();
  if (network.isConnected !== false && network.isInternetReachable !== false) return null;
  return <View style={{ padding: 12, backgroundColor: c.soft }}><Text style={{ color: c.accent, textAlign: 'center', fontSize: 12 }}>Ви офлайн. Збережені рецепти та покупки доступні.</Text></View>;
}
export function RecipeImage({ uri, height = 190 }: { uri: string; height?: number }) {
  const c = useTheme(); const [failedUri, setFailedUri] = useState<string>();

  if (!uri || failedUri === uri) return <View style={{ height, backgroundColor: c.soft, alignItems: 'center', justifyContent: 'center' }}><Ionicons name="restaurant-outline" size={45} color={c.accent} /></View>;
  return <Image source={{ uri }} style={{ width: '100%', height, backgroundColor: c.soft }} contentFit="cover" cachePolicy="memory-disk" transition={180} onError={() => setFailedUri(uri)} />;
}
export function MealCard({ meal }: { meal: MealSummary }) {
  const c = useTheme(), { data } = useApp();
  return <Pressable accessibilityRole="button" accessibilityLabel={`Відкрити рецепт ${meal.name}`} onPress={() => router.push({ pathname: '/meal/[id]', params: { id: meal.id } })}
    style={[styles.card, { backgroundColor: c.card, borderColor: c.line }]}>
    <RecipeImage uri={meal.image} />
    <View style={styles.cardContent}><View style={styles.row}><Text style={[styles.eyebrow, { color: c.accent, flex: 1 }]}>{meal.category || 'РЕЦЕПТ ДНЯ'}</Text>
      <Ionicons name={data.favorites[meal.id] ? 'heart' : 'heart-outline'} size={20} color={c.accent} /></View>
      <Text style={{ color: c.ink, fontWeight: '700', fontSize: 19, lineHeight: 26 }} numberOfLines={2}>{meal.name}</Text>
      <View style={[styles.row, { marginTop: 10 }]}><Ionicons name="globe-outline" size={14} color={c.muted} /><Text style={{ color: c.muted, fontSize: 12, flex: 1 }}>{meal.area || 'Кухні світу'}</Text><Ionicons name="arrow-forward" size={18} color={c.accent} /></View>
    </View></Pressable>;
}
export const styles = StyleSheet.create({
  heading: { paddingHorizontal: 24, paddingTop: 26, paddingBottom: 20, gap: 9 },
  eyebrow: { fontSize: 10, letterSpacing: 2, fontWeight: '700', textTransform: 'uppercase' },
  title: { fontSize: 32, fontWeight: '800', letterSpacing: -1, lineHeight: 39 },
  subtitle: { fontSize: 14, lineHeight: 23 },
  row: { flexDirection: 'row', alignItems: 'center', gap: 8 },
  button: { minHeight: 48, paddingHorizontal: 20, paddingVertical: 13, borderRadius: 15, flexDirection: 'row', gap: 9, alignItems: 'center', justifyContent: 'center' },
  card: { borderRadius: 22, overflow: 'hidden', borderWidth: 1, marginBottom: 18 },
  cardContent: { padding: 18, gap: 9 },
  input: { borderWidth: 1, borderRadius: 14, padding: 14, fontSize: 15, minHeight: 49 },
  label: { fontSize: 13, fontWeight: '600', marginBottom: 8 },
});
