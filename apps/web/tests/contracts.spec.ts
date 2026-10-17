import { test, expect } from '@playwright/test';
import { ApiError, apiMessage, QhApi, validName } from '../src/api';
import { safeReturnPath } from '../src/auth';

test('names follow the existing Unicode code-point contract', () => {
  expect(validName('  Projet QH  ')).toBe(true);
  expect(validName('🧭'.repeat(256))).toBe(true);
  for (const name of ['', '  ', 'a\0b', '🧭'.repeat(257)]) expect(validName(name)).toBe(false);
});
test('return paths cannot redirect off-site or into callbacks', () => {
  for (const path of ['//evil.invalid', 'https://evil.invalid', '/oidc/callback?code=x', '/context-spaces/a?token=x']) expect(safeReturnPath(path)).toBe('/');
  expect(safeReturnPath('/context-spaces/00000000-0000-0000-0000-000000000001')).toBe('/context-spaces/00000000-0000-0000-0000-000000000001');
});
test('REST client sends only the name, fixed same-origin path and bearer; redirects forbidden', async () => {
  const original = globalThis.fetch;
  let call: { path: unknown; init?: RequestInit } | undefined;
  const value = {id:'00000000-0000-0000-0000-000000000001',owner_id:'00000000-0000-0000-0000-000000000002',name:' QH ',status:'active',created_at:'2026-10-17T12:00:00Z',updated_at:'2026-10-17T12:00:00Z'};
  globalThis.fetch = async (path, init) => { call = {path, init}; return new Response(JSON.stringify(value)); };
  try {
    const api = new QhApi(() => 'synthetic-test-only', () => {});
    expect(await api.create(' QH ')).toEqual(value);
    expect(call?.path).toBe('/api/context-spaces');
    expect(call?.init?.body).toBe(JSON.stringify({name:' QH '}));
    expect(call?.init?.credentials).toBe('omit'); expect(call?.init?.redirect).toBe('error');
    await expect(api.get('https://evil.invalid')).rejects.toBeInstanceOf(ApiError);
  } finally { globalThis.fetch = original; }
});
test('errors never render server bodies; 401 invalidates the session', async () => {
  const original = globalThis.fetch; let expired = false;
  globalThis.fetch = async () => new Response('private diagnostic', {status:401});
  try {
    const api = new QhApi(() => 'synthetic-test-only', () => { expired = true; });
    await expect(api.me()).rejects.toMatchObject({status:401});
    expect(expired).toBe(true);
    expect(apiMessage(new Error('private diagnostic'))).not.toContain('private');
  } finally { globalThis.fetch = original; }
});
