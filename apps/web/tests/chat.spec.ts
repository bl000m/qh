import {test,expect} from '@playwright/test';
import {chatAnswer} from '../src/chat';
import {QhApi} from '../src/api';
import type {CanonicalRevision} from '../src/understanding';
const id='00000000-0000-0000-0000-000000000001';
const row:CanonicalRevision={context_space_id:id,item_id:id,revision_id:id,revision_no:1,structural_kind:'item',type_id:'qh.generic.item',type_version:1,content:{text:'Hypothesis'},origin_kind:'ai',validation_state:'proposed',validated_by:null,validated_at:null,current_revision_id:null,is_current_confirmed:false,based_on_revision_id:null,created_at:'2026-10-17T12:00:00Z',temporal:{fact_from:null,fact_to:null,valid_from:null,valid_to:null},relation:null,provenance:[{source_id:id,source_revision_id:id,revision_no:1,origin:{kind:'synthetic'}}]};
const answer={context_id:id,answer:'Proposition non confirmée.',model:'mock',references:[row],provided_revisions:[row],insufficient_context:false,partial_coverage:false,input_bound:1000,context_bytes:500,generation_seconds:0.01};
test('chat wire validator rejects foreign, historical, unsupported and implicit proposed output',()=>{
 expect(chatAnswer(answer,id,true)).toEqual(answer);expect(()=>chatAnswer(answer,id,false)).toThrow();
 for(const change of [{context_id:'foreign'},{references:[{...row,revision_id:'00000000-0000-0000-0000-000000000002'}]},
  {provided_revisions:[{...row,validation_state:'rejected'}]},{references:[]},
  {references:[{...row,content:{text:'Different content'}}]},{input_bound:12001},{context_bytes:8001},
  {model:null},{insufficient_context:'false'}])expect(()=>chatAnswer({...answer,...change},id,true)).toThrow();
});
test('chat transport binds scope and opt-in and never supplies owner/model or credentials in payload',async()=>{
 const original=globalThis.fetch;let observed:any;
 globalThis.fetch=async(path,init)=>{observed={path,init};return new Response(JSON.stringify(answer));};
 try{await new QhApi(()=> 'synthetic-test-only',()=>{}).chat(id,[{role:'user',content:'Question ?'}],true);
  expect(observed.path).toBe('/api/context-spaces/'+id+'/chat');
  expect(JSON.parse(observed.init.body)).toEqual({messages:[{role:'user',content:'Question ?'}],include_proposed:true});
  expect(observed.init.credentials).toBe('omit');expect(observed.init.redirect).toBe('error');
 }finally{globalThis.fetch=original;}
});
