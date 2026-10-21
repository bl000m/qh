import {recognizedCitations} from './understanding';
import type {CanonicalRevision,Json} from './understanding';
export interface QualifiedAssignment {dimension:'thematic'|'semantic_role';value:string;certainty:'asserted'|'tentative';evidence_refs:number[];review_state:'proposed'|'accepted'|'rejected';name_candidate?:string}
export function qualifiedAssignments(row:CanonicalRevision):{index:number;assignment:QualifiedAssignment}[]{
 if(row.type_version!==2||!['qh.generic.item','qh.generic.entity','qh.generic.relation'].includes(row.type_id)||!Array.isArray(row.content.descriptors)||!Array.isArray(row.content.citations))return [];
 const citations=row.content.citations,recognized=recognizedCitations(row);
 return row.content.descriptors.flatMap((value:Json,index)=>{
  if(!value||typeof value!=='object'||Array.isArray(value))return [];
  const d=value as unknown as QualifiedAssignment;
  if(!['thematic','semantic_role'].includes(d.dimension)||typeof d.value!=='string'||!d.value.trim()||!['asserted','tentative'].includes(d.certainty)||!['proposed','accepted','rejected'].includes(d.review_state)||!Array.isArray(d.evidence_refs)||!d.evidence_refs.length||d.evidence_refs.some(i=>!Number.isInteger(i)||i<0||i>=citations.length||!recognized.some(c=>Object.is(c,citations[i])))||new Set(d.evidence_refs).size!==d.evidence_refs.length||d.name_candidate!==undefined&&typeof d.name_candidate!=='string')return [];
  return [{index,assignment:d}];
 });
}
export function thematicGroups(rows:CanonicalRevision[]){
 const groups=new Map<string,{value:string;assignments:QualifiedAssignment[];members:CanonicalRevision[]}>();
 for(const row of rows)for(const {assignment:d} of qualifiedAssignments(row)){
  if(d.dimension!=='thematic'||d.review_state==='rejected'||d.name_candidate!==undefined)continue;
  const group=groups.get(d.value)??{value:d.value,assignments:[],members:[]};group.assignments.push(d);
  if(!group.members.some(r=>r.revision_id===row.revision_id))group.members.push(row);
  groups.set(d.value,group);
 }
 return [...groups.values()].sort((a,b)=>a.value.localeCompare(b.value,'fr'));
}
