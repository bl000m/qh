import {test,expect} from '@playwright/test';
import {thematicGroups,qualifiedAssignments} from '../src/thematic';
import {meaning} from '../src/HumanRevision';
import {groupsIn} from '../src/understanding-presentation';
import type {CanonicalRevision,Json} from '../src/understanding';
const source='00000000-0000-0000-0000-000000000001';
const assignment=(value:string,extra:Record<string,Json>={})=>({dimension:'thematic',value,certainty:'tentative',evidence_refs:[0],review_state:'proposed',...extra});
function row(descriptors:Json[],extra:Partial<CanonicalRevision>={}):CanonicalRevision{return {context_space_id:'scope',item_id:'item',revision_id:'revision',revision_no:1,structural_kind:'item',type_id:'qh.generic.item',type_version:2,content:{text:'This text alone must never produce themes',extraction:{key:'qh51',input_sha256:'a'.repeat(64)},citations:[{source_revision_id:source,start:0,end:14,quote:'An exact quote'}],descriptors},origin_kind:'ai',validation_state:'proposed',validated_by:null,validated_at:null,current_revision_id:null,is_current_confirmed:false,based_on_revision_id:null,created_at:'2026-10-21T12:00:00Z',temporal:{fact_from:null,fact_to:null,valid_from:null,valid_to:null},relation:null,provenance:[{source_id:source,source_revision_id:source,revision_no:1,origin:{}}],...extra};}
test('QH-51 map uses multiple explicit themes, never a revision title, role or organizational category',()=>{
 const first=row([assignment('Sommeil'),assignment('Habitudes de vie'),assignment('objectif',{dimension:'semantic_role'})]);const second=row([assignment('Sommeil')],{revision_id:'second',item_id:'second'});
 const groups=thematicGroups([first,second]);expect(groups.map(g=>g.value)).toEqual(['Habitudes de vie','Sommeil']);expect(groups.find(g=>g.value==='Sommeil')!.members).toHaveLength(2);expect(groups.find(g=>g.value==='Habitudes de vie')!.members[0]).toBe(first);
 expect(thematicGroups([row([{value:'decision',certainty:'asserted'}],{type_version:1})])).toEqual([]);expect(thematicGroups([row([])])).toEqual([]);
 expect(groupsIn([first])).toEqual(['Thème : Sommeil','Thème : Habitudes de vie','Rôle : objectif']);
});
test('QH-51 map excludes rejected, unresolved names and invalid evidence, while confirmed item does not accept assignments',()=>{
 const proposed=assignment('Sommeil'),rejected=assignment('Nutrition',{review_state:'rejected'}),alias=assignment('Repos',{name_candidate:'Sommeil'});
 expect(thematicGroups([row([proposed,rejected,alias],{validation_state:'confirmed',is_current_confirmed:true})]).map(g=>g.value)).toEqual(['Sommeil']);expect(qualifiedAssignments(row([proposed,rejected,alias]))).toHaveLength(3);
 expect(thematicGroups([row([assignment('Invented',{evidence_refs:[8]})])])).toEqual([]);
 const foreign=row([proposed]);foreign.provenance=[];expect(thematicGroups([foreign])).toEqual([]);
 expect(meaning(row([assignment('decision',{certainty:'asserted'})]))).toBe('Élément de compréhension');
 expect(meaning(row([assignment('decision',{dimension:'semantic_role',certainty:'asserted'})]))).toBe('Décision déclarée');
});
