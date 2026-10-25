import {qualifiedAssignments} from './thematic';
import {isUuid} from './transport';
import {descriptorAssignment,recognizedCitations} from './understanding';
import type {CanonicalRevision,Json} from './understanding';
export type ContentOrigin='personal'|'interpretation'|'other';
export const jsonObject=(v:Json|undefined):v is Record<string,Json>=>!!v&&typeof v==='object'&&!Array.isArray(v);
/** Exact stored evidence only: a user quotation alone never makes AI interpretation personal. */
export function contentOrigin(row:CanonicalRevision,ownerId?:string):ContentOrigin {
 const properties=row.content.properties,extraction=row.content.extraction,review=row.content.qh_review;
 const uumLiteral=row.type_version===3&&row.type_id==='qh.generic.item'&&jsonObject(extraction)&&extraction.key==='qh51-uum-literal/3';
 const literal=uumLiteral||jsonObject(properties)&&properties.basis==='literal owner-submitted utterance; no semantic inference'&&jsonObject(extraction)&&extraction.key==='qh39-selected-segment/1-resolved';
 if(literal){
  for(const source of row.provenance){
   const meta=source.origin.metadata;
   if(!jsonObject(meta)||meta.provider_mode!==(uumLiteral?'uum-offline-literal/3':'offline-literal/1')||meta.submission_kind!=='owner_selected_browser_segment'||typeof meta.submitted_by!=='string'||!isUuid(meta.submitted_by)||(ownerId!==undefined&&meta.submitted_by!==ownerId)||!Array.isArray(source.origin.turns))continue;
   const userTurns=source.origin.turns.filter(t=>jsonObject(t)&&t.speaker==='user (owner-declared)');
   const quotes=recognizedCitations(row).filter(q=>q.source_revision_id===source.source_revision_id&&userTurns.some(t=>jsonObject(t)&&t.turn_id===q.turn_id&&t.start===q.start&&t.end===q.end));
   const copied=row.origin_kind==='ai'&&quotes.length===1&&quotes[0].quote===row.content.text;
   const corrected=row.origin_kind==='human'&&jsonObject(review)&&['correct','review_primary','review_assignments'].includes(String(review.action))&&review.actor_id===meta.submitted_by&&quotes.length>0;
   if(copied||corrected)return 'personal';
  }
 }
 return row.origin_kind==='ai'&&!literal?'interpretation':'other';
}
export function itemText(row:CanonicalRevision){return typeof row.content.text==='string'?row.content.text:'Contenu structuré disponible dans les détails.';}
export function itemTitle(row:CanonicalRevision){const title=typeof row.content.title==='string'?row.content.title:itemText(row).split('\n')[0];return title.length>76?title.slice(0,73)+'…':title;}
export function itemState(row:CanonicalRevision,ownerId?:string){return row.validation_state==='rejected'?'Refusé':row.is_current_confirmed?'Confirmé':row.validation_state==='proposed'?(contentOrigin(row,ownerId)==='personal'?'Ajouté par vous':'À vérifier'):'Version conservée';}
export function groupsIn(rows:CanonicalRevision[]){return [...new Set(rows.flatMap(r=>[2,3].includes(r.type_version)?qualifiedAssignments(r).filter(({assignment:d})=>d.review_state!=='rejected').map(({assignment:d})=>(d.dimension==='thematic'?'Thème : ':'Rôle : ')+d.value):Array.isArray(r.content.descriptors)?r.content.descriptors.flatMap(d=>{const a=descriptorAssignment(d);return a?[a.value]:[];}):[]))];}
export function sourceLabel(row:CanonicalRevision,ownerId?:string){return contentOrigin(row,ownerId)==='personal'?'Vos propos conservés':row.origin_kind==='ai'?'Source de l’interprétation':'Source conservée';}
