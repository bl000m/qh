import {test,expect} from '@playwright/test';
import {contentOrigin,groupsIn,itemState,itemTitle} from '../src/understanding-presentation';
import type {CanonicalRevision,Json} from '../src/understanding';
const sid='00000000-0000-0000-0000-000000000004',owner='00000000-0000-0000-0000-000000000005';
const literal:CanonicalRevision={context_space_id:'scope',item_id:'item',revision_id:'rev',revision_no:1,structural_kind:'item',type_id:'qh.generic.item',type_version:1,content:{text:'Mon objectif\nConserver une heure pour mon projet.',properties:{basis:'literal owner-submitted utterance; no semantic inference'},extraction:{key:'qh39-selected-segment/1-resolved',input_sha256:'a'.repeat(64)},citations:[{source_revision_id:sid,turn_id:'turn',start:4,end:52,quote:'Mon objectif\nConserver une heure pour mon projet.'}]},origin_kind:'ai',validation_state:'proposed',validated_by:null,validated_at:null,current_revision_id:null,is_current_confirmed:false,based_on_revision_id:null,created_at:'2026-10-20T18:00:00Z',temporal:{fact_from:null,fact_to:null,valid_from:null,valid_to:null},relation:null,provenance:[{source_id:'source',source_revision_id:sid,revision_no:1,origin:{kind:'conversation',acquired_at:'2026-10-20T18:00:00Z',turns:[{turn_id:'turn',speaker:'user (owner-declared)',start:4,end:52}],metadata:{provider_mode:'offline-literal/1',submission_kind:'owner_selected_browser_segment',submitted_by:owner}}}]};
test('QH-54 origin requires exact literal provider, owner, quotation and turn evidence; proposed is never confirmed',()=>{
 expect(contentOrigin(literal,owner)).toBe('personal');expect(itemState(literal)).toBe('Ajouté par vous');expect(literal.validation_state).toBe('proposed');expect(itemTitle(literal)).toBe('Mon objectif');
 expect(contentOrigin(literal,'another-owner')).toBe('other');
 for(const change of [{properties:{}},{extraction:{key:'real-semantic-extraction',input_sha256:'a'.repeat(64)}}] as Record<string,Json>[])expect(contentOrigin({...literal,content:{...literal.content,...change}},owner)).toBe('interpretation');
 for(const change of [{text:'An altered literal copy.'},{citations:[]}] as Record<string,Json>[])expect(contentOrigin({...literal,content:{...literal.content,...change}},owner)).toBe('other');
 const wrongTurn=structuredClone(literal);wrongTurn.provenance[0].origin.turns=[{turn_id:'turn',speaker:'assistant (unverified dialogue)',start:4,end:52}];expect(contentOrigin(wrongTurn,owner)).toBe('other');
 const missingMode=structuredClone(literal);missingMode.provenance[0].origin.metadata={submitted_by:owner};expect(contentOrigin(missingMode,owner)).toBe('other');
});
test('QH-54 origin keeps audited human corrections and never promotes generic human/import content or AI quotations',()=>{
 const corrected={...literal,origin_kind:'human',content:{...literal.content,text:'Mon objectif corrigé',qh_review:{action:'correct',actor_id:owner}}};expect(contentOrigin(corrected,owner)).toBe('personal');expect(corrected.validation_state).toBe('proposed');
 expect(contentOrigin({...corrected,content:{...corrected.content,qh_review:{action:'correct',actor_id:'different'}}},owner)).toBe('other');
 expect(contentOrigin({...literal,origin_kind:'import'},owner)).toBe('other');expect(contentOrigin({...literal,origin_kind:'human',content:{text:'Human contribution without direct declaration provenance'}},owner)).toBe('other');
 expect(itemState({...literal,content:{text:'Semantic interpretation'}})).toBe('À vérifier');
});
test('QH-54 groups contain only actual explicit descriptors, never categories inferred from financial text',()=>{
 expect(groupsIn([literal])).toEqual([]);expect(groupsIn([{...literal,content:{text:'500 EUR savings',descriptors:[{value:'unusual exact meaning',certainty:'tentative'},{value:'decision',certainty:'asserted'}]}}])).toEqual(['unusual exact meaning','decision']);
 expect(groupsIn([{...literal,content:{descriptors:['fake',{value:'empty'}]}}])).toEqual([]);
});
