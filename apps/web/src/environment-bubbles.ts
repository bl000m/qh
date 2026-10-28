import type {Domain, Organization} from './environment';

export interface DomainBubble {
  domain: Domain;
  count: number;
  x: number;
  y: number;
  radius: number;
}
export interface BubbleLabel {width: number; height: number}

// Presentation aliases only: API records, navigation and accessible names stay exact.
export function domainDisplayNames(domains: Domain[]): Record<string, string> {
  const aliases: Record<string, string> = {
    'travail & projets': 'Travail', 'santé & bien-être': 'Santé',
    'finances & démarches': 'Finances', 'apprentissage & évolution': 'Apprentissage',
    'relations & proches': 'Relations', 'vie quotidienne & habitat': 'Vie quotidienne',
    'loisirs & découvertes': 'Loisirs'
  };
  const key = (value: string) => value.normalize('NFC').trim().toLocaleLowerCase('fr');
  const candidates = domains.map(domain => aliases[key(domain.name)] ?? domain.name);
  return Object.fromEntries(domains.map((domain, index) => [domain.id,
    candidates.filter(name => key(name) === key(candidates[index])).length === 1 ? candidates[index] : domain.name]));
}

export interface ReservedArea {width: number; height: number}
const points = Array.from({length: 601}, (_, index) => {
  const angle = index * Math.PI * (3 - Math.sqrt(5)), distance = Math.sqrt(index / 600) * .48;
  return {x: .5 + Math.cos(angle) * distance, y: .5 + Math.sin(angle) * distance};
});
function labelBounds(bubble: DomainBubble, label: BubbleLabel) {
  return {left: bubble.x - label.width / 2, right: bubble.x + label.width / 2,
    top: bubble.y + bubble.radius * .68, bottom: bubble.y + bubble.radius * .68 + label.height};
}
function clearOfLabel(circle: DomainBubble, box: ReturnType<typeof labelBounds>) {
  const x = Math.max(box.left, Math.min(circle.x, box.right)), y = Math.max(box.top, Math.min(circle.y, box.bottom));
  return Math.hypot(circle.x - x, circle.y - y) > circle.radius + 20;
}
function separated(a: DomainBubble, b: DomainBubble, labels: Record<string, BubbleLabel>) {
  if (Math.hypot(a.x - b.x, a.y - b.y) < a.radius + b.radius + 24) return false;
  const first = labelBounds(a, labels[a.domain.id]), second = labelBounds(b, labels[b.domain.id]);
  if (!(first.right + 20 < second.left || second.right + 20 < first.left || first.bottom + 20 < second.top || second.bottom + 20 < first.top)) return false;
  return clearOfLabel(a, second) && clearOfLabel(b, first);
}
function pack(domains: DomainBubble[], labels: Record<string, BubbleLabel>, width: number, height: number, reserved: ReservedArea, scale: number) {
  const placed: DomainBubble[] = [];
  for (const [index, domain] of [...domains].sort((a, b) => b.radius - a.radius || a.domain.id.localeCompare(b.domain.id)).entries()) {
    const radius = domain.radius * scale, angle = index * 2.4 + 2.1;
    const target = index ? {x: .52 + Math.cos(angle) * .30, y: .54 + Math.sin(angle) * .30} : {x: .59, y: .38};
    const candidates = points.map(point => ({...domain, radius, x: point.x * width, y: point.y * height}));
    candidates.sort((a, b) => Math.hypot(a.x / width - target.x, a.y / height - target.y) - Math.hypot(b.x / width - target.x, b.y / height - target.y));
    const position = candidates.find(bubble => {
      const label = labelBounds(bubble, labels[bubble.domain.id]);
      if (bubble.x - radius * 1.25 < 16 || bubble.x + radius * 1.25 > width - 16 || bubble.y - radius * 1.14 < 16 || bubble.y + radius * 1.45 > height - 16) return false;
      if (label.left < 16 || label.right > width - 16 || label.bottom > height - 16) return false;
      if (reserved.height && Math.min(bubble.x - radius * 1.25, label.left) < reserved.width + 16 && Math.min(bubble.y - radius * 1.14, label.top) < reserved.height + 16) return false;
      return placed.every(other => separated(bubble, other, labels));
    });
    if (!position) return null;
    placed.push(position);
  }
  return domains.map(domain => placed.find(bubble => bubble.domain.id === domain.domain.id)!);
}
export function domainHoverScale(bubble: DomainBubble, width: number, height: number, reserved: ReservedArea): number {
  const {x, y, radius} = bubble;
  let limit = Math.min(1.6, (x - 12) / (1.25 * radius), (width - x - 12) / (1.25 * radius),
    (y - 12) / (1.14 * radius), (height - y - 12) / (1.45 * radius));
  if (reserved.height) limit = Math.min(limit, Math.max((x - reserved.width - 12) / (1.25 * radius), (y - reserved.height - 12) / (1.14 * radius)));
  return Math.max(1, limit);
}
export function domainBubbles(organization: Organization, measured: Record<string, BubbleLabel> = {}, width = 800, height = 650, reserved: ReservedArea = {width: 0, height: 0}): DomainBubble[] {
  const counts = new Map(organization.domains.map(domain => [domain.id, 0]));
  for (const memberships of Object.values(organization.memberships)) {
    for (const id of memberships) counts.set(id, (counts.get(id) ?? 0) + 1);
  }
  const maximum = Math.max(1, ...counts.values()), names = domainDisplayNames(organization.domains);
  const labels = Object.fromEntries(organization.domains.map(domain => [domain.id, measured[domain.id] ?? {width: names[domain.id].length * 8 + 34, height: 44}]));
  const base = Math.max(44, Math.min(88, width * .105, height * .13) * Math.min(1, Math.sqrt(10 / Math.max(1, organization.domains.length))));
  const domains = organization.domains.map(domain => ({domain, count: counts.get(domain.id)!, x: 0, y: 0,
    radius: base * (1 + .65 * Math.log1p(counts.get(domain.id)!) / Math.log1p(maximum))}));
  if (width >= 480) {
    for (let scale = 1; scale >= Math.max(.58, 34 / base); scale -= .06) {
      const result = pack(domains, labels, width, height, reserved, scale);
      if (result) return result;
    }
  }
  // Narrow or very dense views keep every domain accessible in a staggered column.
  let top = reserved.height + 24;
  return domains.map((domain, index) => {
    const radius = Math.min(domain.radius, width * .23), label = labels[domain.domain.id];
    const half = Math.max(radius * 1.25, label.width / 2) + 16;
    const x = Math.max(half, Math.min(width - half, width / 2 + Math.sin(index * 2.4) * width * .12));
    const bubble = {...domain, radius, x, y: top + radius * 1.14};
    top = Math.max(bubble.y + radius * 1.45, labelBounds(bubble, label).bottom) + 32;
    return bubble;
  });
}
