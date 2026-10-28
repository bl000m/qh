import type {Domain, Organization} from './environment';

export interface DomainBubble {
  domain: Domain;
  count: number;
  x: number;
  y: number;
  radius: number;
}
export interface BubbleLabel {width: number; height: number}

// Pixel footprints include labels, drift, hover and keyboard focus. The artwork
// behind them is decorative and imposes no circular boundary on navigation.
function arrange(domains: DomainBubble[], labels: Record<string, BubbleLabel>, width: number, scale: number): DomainBubble[] {
  const rows: {bubble: DomainBubble; width: number; height: number}[][] = [[]];
  for (const domain of domains) {
    const radius = domain.radius * scale;
    const label = labels[domain.domain.id] ?? {width: domain.domain.name.length * 8.5 + 40, height: 52};
    const item = {bubble: {...domain, radius}, width: Math.max(2 * radius, label.width) + 24, height: Math.max(2 * radius, label.height) + 24};
    const row = rows.at(-1)!;
    const used = row.reduce((sum, value) => sum + value.width + 40, 0);
    if (row.length && used + item.width > width - 32) rows.push([item]);
    else row.push(item);
  }
  let top = 16;
  return rows.flatMap((row, rowIndex) => {
    const total = row.reduce((sum, item) => sum + item.width, 0);
    const gap = Math.max(40, (width - 32 - total) / (row.length + 1));
    let left = (width - total - gap * (row.length - 1)) / 2;
    const height = Math.max(0, ...row.map(item => item.height));
    const placed = row.map((item, index) => {
      const bubble = {...item.bubble, x: left + item.width / 2, y: top + height / 2 + ((index + rowIndex) % 3 - 1) * 8};
      left += item.width + gap;
      return bubble;
    });
    top += height + 48;
    return placed;
  });
}

export function domainBubbles(organization: Organization, labels: Record<string, BubbleLabel> = {}, width = 800, height = 650): DomainBubble[] {
  const counts = new Map(organization.domains.map(domain => [domain.id, 0]));
  for (const memberships of Object.values(organization.memberships)) {
    for (const id of memberships) counts.set(id, (counts.get(id) ?? 0) + 1);
  }
  const maximum = Math.max(1, ...counts.values());
  const base = Math.max(40, 52 * Math.min(1, Math.max(.74, width / 600), Math.sqrt(12 / Math.max(1, organization.domains.length))));
  const domains = organization.domains.map(domain => ({domain, count: counts.get(domain.id)!, x: 0, y: 0,
    radius: base * (1 + .65 * Math.log1p(counts.get(domain.id)!) / Math.log1p(maximum))}));
  let scale = 1;
  let result = arrange(domains, labels, width, scale);
  while (result.some(bubble => bubble.y + bubble.radius + 16 > height) && scale > 40 / base + 1e-6) {
    scale = Math.max(40 / base, scale * .92);
    result = arrange(domains, labels, width, scale);
  }
  return result;
}
