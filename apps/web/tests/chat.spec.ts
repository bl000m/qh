import {test,expect} from '@playwright/test';
import {chatAnswer} from '../src/chat';
import {QhApi} from '../src/api';
import type {CanonicalRevision} from '../src/understanding';
const id='00000000-0000-0000-0000-000000000001';
const row:CanonicalRevision={context_space_id:id,item_id:id,revision_id:id,revision_no:1,structural_kind:'item',type_id:'qh.generic.item',type_version:1,content:{text:'Hypothesis'},origin_kind:'ai',validation_state:'proposed',validated_by:null,validated_at:null,current_revision_id:null,is_current_confirmed:false,based_on_revision_id:null,created_at:'2026-10-17T12:00:00Z',temporal:{fact_from:null,fact_to:null,valid_from:null,valid_to:null},relation:null,provenance:[{source_id:id,source_revision_id:id,revision_no:1,origin:{kind:'synthetic'}}]};
const answer={context_id:id,answer:'Proposition non confirmée.',model:'mock',references:[row],provided_revisions:[row],support_basis:'canonical',insufficient_context:false,partial_coverage:false,input_bound:1000,context_bytes:500,generation_seconds:0.01};
test('chat wire validator rejects foreign, historical, unsupported and implicit proposed output',()=>{
 expect(chatAnswer(answer,id,true,[{role:'user',content:'Question'}])).toEqual(answer);expect(()=>chatAnswer(answer,id,false,[{role:'user',content:'Question'}])).toThrow();
 for(const change of [{context_id:'foreign'},{references:[{...row,revision_id:'00000000-0000-0000-0000-000000000002'}]},
  {provided_revisions:[{...row,validation_state:'rejected'}]},{references:[]},
  {references:[{...row,content:{text:'Different content'}}]},{input_bound:12001},{context_bytes:8001},
  {model:null},{insufficient_context:'false'}])expect(()=>chatAnswer({...answer,...change},id,true,[{role:'user',content:'Question'}])).toThrow();
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

test('support basis checks actual dialogue and exact cited canonical records without promoting facts',()=>{
 const messages=[{role:'user' as const,content:'Informations explicitement envoyées.'}];
 const dialogue={...answer,support_basis:'dialogue',references:[],provided_revisions:[],insufficient_context:false};
 expect(chatAnswer(dialogue,id,false,messages).support_basis).toBe('dialogue');
 expect(()=>chatAnswer(dialogue,id,false,[])).toThrow();
 for(const change of [{support_basis:'canonical'},{support_basis:'mixed'},
  {support_basis:'invented'},{support_basis:undefined},{references:[row],provided_revisions:[row]}])expect(()=>chatAnswer({...dialogue,...change},id,true,messages)).toThrow();
 expect(chatAnswer({...answer,support_basis:'mixed'},id,true,messages).support_basis).toBe('mixed');
 expect(()=>chatAnswer({...answer,support_basis:'mixed'},id,true,[])).toThrow();
 expect(chatAnswer({...dialogue,support_basis:'insufficient',insufficient_context:true},id,false,messages).insufficient_context).toBe(true);
});

test('support provenance and insufficient context are independent without bypassing citation integrity',()=>{
 const messages=[{role:'user' as const,content:'Informations explicites, question encore partiellement ouverte.'}];
 for(const insufficient_context of [false,true]){
  for(const support_basis of ['dialogue','insufficient']){
   const value={...answer,support_basis,insufficient_context,references:[],provided_revisions:[]};
   expect(chatAnswer(value,id,false,messages)).toEqual(value);
  }
  for(const support_basis of ['canonical','mixed']){
   expect(chatAnswer({...answer,support_basis,insufficient_context},id,true,messages).insufficient_context).toBe(insufficient_context);
   expect(()=>chatAnswer({...answer,support_basis,insufficient_context,references:[]},id,true,messages)).toThrow();
  }
 }
 expect(()=>chatAnswer({...answer,support_basis:'dialogue',insufficient_context:true,references:[],provided_revisions:[]},id,false,[])).toThrow();
});

test('general knowledge is accepted without attributing it to a Space or bypassing exact citations',()=>{
 const messages=[{role:'user' as const,content:'Proponimi una lista della spesa per fare un risotto'}];
 const general={...answer,answer:'Riso Carnaroli, brodo, cipolla, burro, Parmigiano.',support_basis:'general',references:[],provided_revisions:[]};
 expect(chatAnswer(general,id,false,messages).support_basis).toBe('general');
 expect(chatAnswer({...general,provided_revisions:[row]},id,true,messages).references).toHaveLength(0);
 expect(()=>chatAnswer({...general,references:[row],provided_revisions:[row]},id,true,messages)).toThrow();
 expect(()=>chatAnswer({...answer,references:[{...row,context_space_id:'00000000-0000-0000-0000-000000000099'}]},id,true,messages)).toThrow();
 expect(()=>chatAnswer({...general,support_basis:'canonical'},id,true,messages)).toThrow();
});
