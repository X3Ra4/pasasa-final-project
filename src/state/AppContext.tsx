import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, PropsWithChildren, useContext, useEffect, useSyncExternalStore } from 'react';
import { createStore } from '@/core/store';

const store = createStore(AsyncStorage);
const AppContext = createContext(store);
export function AppProvider({ children }: PropsWithChildren) {
  useEffect(() => { void store.load(); }, []);
  return <AppContext.Provider value={store}>{children}</AppContext.Provider>;
}
export function useApp() {
  const value = useContext(AppContext);
  const snapshot = useSyncExternalStore(value.subscribe, value.getSnapshot, value.getSnapshot);
  return { ...snapshot, update: value.update, reset: value.reset, reload: value.load, dismissError: value.dismissError };
}
