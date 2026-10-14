import { useApp } from '@/state/AppContext';

const light = { bg: '#FBF8F3', card: '#FFFFFF', ink: '#282B24', muted: '#797C70', accent: '#C85C35',
  soft: '#F6E9DF', line: '#E8E6DE', green: '#526C4F', greenSoft: '#EBEFE4', danger: '#B43F39', white: '#FFFFFF' };
const dark: typeof light = { bg: '#191E1A', card: '#252D26', ink: '#F3F0E8', muted: '#B0B9AA', accent: '#F29B72',
  soft: '#3C3028', line: '#3B443A', green: '#A8C28F', greenSoft: '#303E2E', danger: '#FF9990', white: '#191E1A' };
export function useTheme() { return useApp().data.theme === 'dark' ? dark : light; }
