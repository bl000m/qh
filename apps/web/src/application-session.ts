import {useEffect, useRef, useState, useSyncExternalStore} from 'react';
import type {BrowserSession} from './auth';
import {apiMessage, type QhApi} from './api';
import type {Organization} from './environment';
import {drafts} from './drafts';

interface Bootstrap {identity: string; organization?: Organization}
export type ApplicationPhase = 'initializing' | 'authenticated' | 'unauthenticated' | 'error';

export function useApplicationSession(session: BrowserSession, api: QhApi) {
  const state = useSyncExternalStore(session.subscribe, session.snapshot);
  const pending = useRef<Promise<Bootstrap> | null>(null);
  const [bootstrap, setBootstrap] = useState<Bootstrap | null>(null);
  const [error, setError] = useState('');
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {void session.initialize();}, [session]);
  useEffect(() => {
    if (state !== 'authenticated') {
      if (state === 'anonymous' || state === 'signed-out') {pending.current = null; setBootstrap(null); setError('');}
      return;
    }
    let active = true;
    pending.current ??= api.me().then(async identity => {
      if (session.snapshot() !== 'authenticated') throw new Error('Session changed');
      const organization = window.location.pathname === '/' ? await api.organization() : undefined;
      return {identity, organization};
    });
    pending.current.then(value => {if (active) {drafts.verifyOwner(value.identity); setBootstrap(value);}}, reason => {if (active) setError(apiMessage(reason));});
    return () => {active = false;};
  }, [session, api, state, attempt]);
  let phase: ApplicationPhase = 'initializing';
  if (state === 'anonymous' || state === 'signed-out') phase = 'unauthenticated';
  else if (state === 'error' || error || state === 'expired' && !(session.preserveDrafts && bootstrap)) phase = 'error';
  else if ((state === 'authenticated' || state === 'expired') && bootstrap) phase = 'authenticated';
  const retry = () => {pending.current = null; setError(''); setAttempt(value => value + 1);};
  return {phase, state, bootstrap, error, retry};
}
