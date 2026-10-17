import { useSyncExternalStore } from 'react';
function subscribe(listener: () => void) {
  window.addEventListener('popstate', listener);
  return () => window.removeEventListener('popstate', listener);
}
export function usePath() { return useSyncExternalStore(subscribe, () => window.location.pathname); }
export function navigate(path: string) {
  window.history.pushState(null, '', path);
  window.dispatchEvent(new PopStateEvent('popstate'));
}
