import { router } from 'expo-router';
import { Empty, Page } from '@/ui/components';
export default function NotFound() { return <Page><Empty title="Сторінку не знайдено" text="Повернімося до кулінарного натхнення." action="На головну" onPress={() => router.replace('/')} /></Page>; }
