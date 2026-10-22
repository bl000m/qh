import { ApiError, isUuid } from './transport';
export type RevisionView = 'current' | 'proposed' | 'history';
export type Json = null | boolean | number | string | Json[] | { [key: string]: Json };
export interface SourceRevision {
  source_id: string; source_revision_id: string; revision_no: number; origin: Record<string, Json>;
}
export interface RevisionRelation {
  predicate: string; source_item_id: string; source_revision_id: string;
  target_item_id: string; target_revision_id: string;
}
export interface CanonicalRevision {
  context_space_id: string; item_id: string; revision_id: string; revision_no: number;
  structural_kind: 'item' | 'entity' | 'relation'; type_id: string; type_version: number;
  content: Record<string, Json>; origin_kind: string; validation_state: 'proposed' | 'confirmed' | 'rejected';
  validated_by: string | null; validated_at: string | null; current_revision_id: string | null;
  is_current_confirmed: boolean; based_on_revision_id: string | null; created_at: string;
  temporal: { fact_from: string | null; fact_to: string | null; valid_from: string | null; valid_to: string | null };
  relation: RevisionRelation | null; provenance: SourceRevision[];
}
export interface RevisionQuery {
  context_ids: string[]; view: RevisionView; text?: string; descriptors?: string[];
  include_tentative?: boolean; limit: number; after_revision_id?: string;
}
export interface RevisionPage { view: RevisionView; items: CanonicalRevision[]; next_after_revision_id: string | null }
export interface BrowseQuery {
  view: RevisionView; limit: number; after_revision_id?: string; descriptor?: string;
  descriptor_dimension?: 'thematic' | 'semantic_role'; latest_pending?: boolean;
  primary_dimension?: string; primary_unclassified?: boolean;
  include_tentative?: boolean; kind?: 'item' | 'entity' | 'relation'; unclassified?: boolean;
  item_id?: string; revision_id?: string; related_item_id?: string;
}
export interface Citation { source_revision_id: string; start: number; end: number; quote: string; turn_id?: string }
const object = (v: unknown): v is Record<string, Json> => !!v && typeof v === 'object' && !Array.isArray(v);
const uuid = (v: unknown) => typeof v === 'string' && isUuid(v);
const positive = (v: unknown) => typeof v === 'number' && Number.isInteger(v) && v > 0;
const time = (v: unknown) => v === null || typeof v === 'string' && Number.isFinite(Date.parse(v));
export function descriptorAssignment(value: Json): {value: string; certainty: 'asserted' | 'tentative'} | null {
  if (!object(value) || typeof value.value !== 'string' || !value.value ||
      (value.certainty !== 'asserted' && value.certainty !== 'tentative')) return null;
  return {value:value.value,certainty:value.certainty};
}
export function descriptorValues(input: string): string[] {
  // One literal descriptor per line. Never trim, fold case or normalize meaning.
  return input.split('\n').filter(value => value.length > 0);
}
export function recognizedCitations(revision: CanonicalRevision): Citation[] {
  const { extraction, citations } = revision.content;
  if (!object(extraction) || typeof extraction.key !== 'string' || typeof extraction.input_sha256 !== 'string' || !Array.isArray(citations)) return [];
  return citations.filter((v): v is Json & Citation => object(v) && uuid(v.source_revision_id) &&
    revision.provenance.some(s => s.source_revision_id === v.source_revision_id) &&
    typeof v.quote === 'string' && v.quote.length > 0 && typeof v.start === 'number' &&
    Number.isInteger(v.start) && v.start >= 0 && typeof v.end === 'number' && Number.isInteger(v.end) && v.end > v.start) as Citation[];
}
export function revisionPage(raw: unknown, query: RevisionQuery): RevisionPage {
  const p = raw as RevisionPage;
  if (!p || p.view !== query.view || !Array.isArray(p.items) || p.items.length > query.limit ||
      !(p.next_after_revision_id === null || uuid(p.next_after_revision_id))) throw new ApiError(502);
  const seen = new Set<string>();
  for (const r of p.items) {
    if (!r || !uuid(r.revision_id) || !uuid(r.item_id) || !query.context_ids.includes(r.context_space_id) || seen.has(r.revision_id) ||
        !positive(r.revision_no) || !['item','entity','relation'].includes(r.structural_kind) || !object(r.content) ||
        typeof r.type_id !== 'string' || !positive(r.type_version) || typeof r.origin_kind !== 'string' ||
        !['proposed','confirmed','rejected'].includes(r.validation_state) || typeof r.is_current_confirmed !== 'boolean' ||
        !time(r.created_at) || !r.temporal || !Object.values(r.temporal).every(time) ||
        !Array.isArray(r.provenance) || !r.provenance.every(s => uuid(s.source_id) && uuid(s.source_revision_id) && positive(s.revision_no) && object(s.origin)) ||
        (query.view === 'current' && (!r.is_current_confirmed || r.validation_state !== 'confirmed')) ||
        (query.view === 'proposed' && r.validation_state !== 'proposed')) throw new ApiError(502);
    if ((r.structural_kind === 'relation') !== (r.relation !== null)) throw new ApiError(502);
    if (r.relation && (typeof r.relation.predicate !== 'string' || !r.relation.predicate ||
        ![r.relation.source_item_id,r.relation.source_revision_id,r.relation.target_item_id,r.relation.target_revision_id].every(uuid))) throw new ApiError(502);
    seen.add(r.revision_id);
  }
  return p;
}
