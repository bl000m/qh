import {test, expect} from '@playwright/test';
import {domainBubbles} from '../src/environment-bubbles';
import type {Organization} from '../src/environment';

const id = (index: number) => `00000000-0000-0000-0000-${String(index).padStart(12, '0')}`;
function organization(count: number): Organization {
  const domains = Array.from({length: count}, (_, index) => ({id: id(index + 1), name: `Domaine ${index + 1}`}));
  const memberships = Object.fromEntries(Array.from({length: 1000}, (_, index) => [id(index + 100), domains.filter((_, d) => index < d * d).map(domain => domain.id)]));
  return {version: 1, domains, memberships, primary_domains: {}, usage: {}};
}

test('real multi-domain memberships determine bounded, monotonic bubble sizes', () => {
  const document = organization(8);
  const bubbles = domainBubbles(document);
  expect(bubbles.map(bubble => bubble.domain.id)).toEqual(document.domains.map(domain => domain.id));
  expect(bubbles.map(bubble => bubble.count)).toEqual([0, 1, 4, 9, 16, 25, 36, 49]);
  expect(bubbles[0].radius).toBeGreaterThan(0);
  for (let index = 1; index < bubbles.length; index++) expect(bubbles[index].radius).toBeGreaterThan(bubbles[index - 1].radius);
  expect(bubbles.at(-1)!.radius / bubbles[0].radius).toBeLessThanOrEqual(1.65);
  expect(domainBubbles(document)).toEqual(bubbles);
});

test('zero to fifty domains use the available width without overlap, including drift clearance', () => {
  for (const count of [0, 1, 2, 5, 7, 12, 20, 35, 50]) {
    const bubbles = domainBubbles(organization(count));
    expect(bubbles).toHaveLength(count);
    for (const [index, bubble] of bubbles.entries()) {
      expect(bubble.radius).toBeGreaterThan(0);
      expect(bubble.x - bubble.radius).toBeGreaterThanOrEqual(0);
      expect(bubble.x + bubble.radius).toBeLessThanOrEqual(800);
      for (const other of bubbles.slice(index + 1)) expect(Math.hypot(bubble.x - other.x, bubble.y - other.y)).toBeGreaterThanOrEqual(bubble.radius + other.radius + 20);
    }
  }
});
