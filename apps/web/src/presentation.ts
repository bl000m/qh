/** Display only: canonical names, IDs and accessible link names stay intact. */
export function spaceTitle(name: string): string {
  const characters = [...new Intl.Segmenter('fr', {granularity: 'grapheme'}).segment(name)].map(part => part.segment);
  return characters.length > 10 ? characters.slice(0, 10).join('') + '…' : name;
}
