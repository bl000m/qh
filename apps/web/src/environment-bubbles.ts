import type {Domain, Organization} from './environment';

export interface DomainBubble {
  domain: Domain;
  count: number;
  x: number;
  y: number;
  radius: number;
}

// Disk coordinates reserve space for drift, hover and the keyboard focus ring.
const clearance = .025;
const candidates = Array.from({length: 401}, (_, index) => {
  const distance = .92 * Math.sqrt(index / 400);
  const angle = index * Math.PI * (3 - Math.sqrt(5));
  return {x: Math.cos(angle) * distance, y: Math.sin(angle) * distance};
});
const orderedCandidates = Array.from({length: 50}, (_, index) => {
  const angle = index * Math.PI * (3 - Math.sqrt(5)) - .7;
  const target = {x: Math.cos(angle) * .45, y: Math.sin(angle) * .45};
  return [...candidates].sort((a, b) => Math.hypot(a.x - target.x, a.y - target.y) - Math.hypot(b.x - target.x, b.y - target.y));
});

function pack(domains: DomainBubble[], scale: number): DomainBubble[] | null {
  const placed: DomainBubble[] = [];
  for (const [index, domain] of domains.entries()) {
    const radius = domain.radius * scale;
    const position = orderedCandidates[index].find(point =>
      Math.hypot(point.x, point.y) + radius + clearance <= .96 &&
      placed.every(other => Math.hypot(point.x - other.x, point.y - other.y) >= radius + other.radius + 2 * clearance));
    if (!position) return null;
    placed.push({...domain, ...position, radius});
  }
  return placed;
}

export function domainBubbles(organization: Organization): DomainBubble[] {
  const counts = new Map(organization.domains.map(domain => [domain.id, 0]));
  for (const memberships of Object.values(organization.memberships)) {
    for (const id of memberships) counts.set(id, (counts.get(id) ?? 0) + 1);
  }
  const maximum = Math.max(1, ...counts.values());
  const domains = organization.domains.map(domain => ({domain, count: counts.get(domain.id)!, x: 0, y: 0,
    radius: 1 + .65 * Math.log1p(counts.get(domain.id)!) / Math.log1p(maximum)}));
  domains.sort((a, b) => b.radius - a.radius || a.domain.id.localeCompare(b.domain.id));
  let low = 0, high = .64 / Math.max(1, ...domains.map(domain => domain.radius));
  let result: DomainBubble[] = [];
  for (let attempt = 0; attempt < 14; attempt++) {
    const scale = (low + high) / 2;
    const packed = pack(domains, scale);
    if (packed) { low = scale; result = packed; } else high = scale;
  }
  // Preserve the owner's keyboard order rather than sorting by bubble size.
  return organization.domains.map(domain => result.find(bubble => bubble.domain.id === domain.id)!);
}
