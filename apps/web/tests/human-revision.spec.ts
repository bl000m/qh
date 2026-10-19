import {test,expect} from '@playwright/test';
import {renderToStaticMarkup} from 'react-dom/server';
import {createElement} from 'react';
import {HumanRevision,meaning,quotationSpeakers,validationLabel} from '../src/HumanRevision';
import type {CanonicalRevision} from '../src/understanding';
const row:CanonicalRevision={context_space_id:'space',item_id:'item',revision_id:'revision',revision_no:1,structural_kind:'item',type_id:'qh.generic.item',type_version:1,content:{text:'Un essai pourrait aider.',descriptors:[{value:'hypothesis',certainty:'asserted'}],extraction:{key:'fixture',input_sha256:'a'.repeat(64)},citations:[{source_revision_id:'00000000-0000-0000-0000-000000000004',quote:'Un essai pourrait aider.',start:0,end:23,turn_id:'t1'}]},origin_kind:'ai',validation_state:'proposed',validated_by:null,validated_at:null,current_revision_id:null,is_current_confirmed:false,based_on_revision_id:null,created_at:'2026-10-19T00:00:00Z',temporal:{fact_from:null,fact_to:null,valid_from:null,valid_to:null},relation:null,provenance:[{source_id:'source',source_revision_id:'00000000-0000-0000-0000-000000000004',revision_no:1,origin:{turns:[{turn_id:'t1',speaker:'Alex'}]}}]};
test('human provenance keeps exact meaning, speaker versus actor and hidden full record',()=>{
 expect(meaning(row)).toBe('Hypothèse');expect(quotationSpeakers(row)).toEqual(['Alex']);
 expect(validationLabel(row)).toBe('Proposition non confirmée');
 const html=renderToStaticMarkup(createElement(HumanRevision,{row}));
 expect(html).toContain('Cela n’attribue pas automatiquement');expect(html).toContain('Enregistrement canonique complet');
 expect(html.indexOf('Un essai pourrait aider.')).toBeLessThan(html.indexOf('Détails techniques'));
 expect(html).not.toContain('Fait — à partir du');
});
test('unknown, tentative and differently spelled descriptors never infer a category',()=>{
 for(const value of ['Hypothesis','decision ','new-meaning'])expect(meaning({...row,content:{descriptors:[{value,certainty:'asserted'}]}})).toBe('Élément de compréhension');
 expect(meaning({...row,content:{descriptors:[{value:'decision',certainty:'tentative'}]}})).toBe('Élément de compréhension');
 expect(quotationSpeakers({...row,provenance:[{...row.provenance[0],origin:{turns:[{turn_id:'t1',speaker:'Alex'},{turn_id:'t1',speaker:'Bob'}]}}]})).toEqual([]);
 expect(validationLabel({...row,validation_state:'confirmed',is_current_confirmed:true})).toBe('Confirmée actuellement dans QH');
});
