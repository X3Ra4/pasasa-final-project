import { useCallback, useEffect, useRef, useState } from 'react';

export function useRequest<T>(loader: (signal: AbortSignal) => Promise<T>, initial: T) {
  const [data, setData] = useState(initial);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');
  const active = useRef<AbortController | null>(null);
  const run = useCallback(async (refresh = false) => {
    active.current?.abort();
    const controller = new AbortController(); active.current = controller;
    setError(''); setLoading(!refresh); setRefreshing(refresh);
    try {
      const next = await loader(controller.signal);
      if (!controller.signal.aborted) setData(next);
    } catch (error) {
      if (!controller.signal.aborted) setError(error instanceof Error ? error.message : 'Не вдалося завантажити дані.');
    } finally {
      if (!controller.signal.aborted) { setLoading(false); setRefreshing(false); }
    }
  }, [loader]);
  useEffect(() => { const scheduled = setTimeout(() => { void run(); }, 0); return () => { clearTimeout(scheduled); active.current?.abort(); }; }, [run]);
  return { data, loading, refreshing, error, retry: () => void run(), refresh: () => void run(true) };
}
