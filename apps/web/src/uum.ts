import type {CanonicalRevision} from './understanding';
import {recognizedCitations} from './understanding';
export const DIMENSIONS = [
 ['situation_information','Situation & informations'],
 ['objectives_intentions','Objectifs & intentions'],
 ['decisions_actions','Décisions & actions'],
 ['constraints_preferences','Contraintes & préférences'],
 ['hypotheses_uncertainties','Hypothèses & incertitudes'],
 ['open_questions','Questions ouvertes']
] as const;
export type PrimaryDimension=typeof DIMENSIONS[number][0];
export const dimensionLabel=(id:string)=>DIMENSIONS.find(([value])=>value===id)?.[1]??id;
export function primaryAssignment(row:CanonicalRevision){
 const value=row.content.primary_dimension;
 if(row.type_version!==3||!['qh.generic.item','qh.generic.entity','qh.generic.relation'].includes(row.type_id)||!value||typeof value!=='object'||Array.isArray(value))return null;
 const p=value as {value:PrimaryDimension;certainty:'asserted'|'tentative';review_state:'proposed'|'accepted'|'rejected';evidence_refs:number[]};
 const citations=Array.isArray(row.content.citations)?row.content.citations:[],recognized=recognizedCitations(row);
 if(!DIMENSIONS.some(([id])=>id===p.value)||!['asserted','tentative'].includes(p.certainty)||!['proposed','accepted','rejected'].includes(p.review_state)||!Array.isArray(p.evidence_refs)||!p.evidence_refs.length||p.evidence_refs.some(i=>!Number.isInteger(i)||!recognized.some(c=>Object.is(c,citations[i]))))return null;
 return p;
}
