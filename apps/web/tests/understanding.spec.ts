import { test, expect } from '@playwright/test';
import { descriptorAssignment, descriptorValues, recognizedCitations, revisionPage } from '../src/understanding';
import type { CanonicalRevision, Json } from '../src/understanding';
import { QhApi } from '../src/api';
const id='00000000-0000-0000-0000-000000000001';
const row:CanonicalRevision={context_space_id:id,item_id:id,revision_id:id,revision_no:1,structural_kind:'item',type_id:'qh.generic.item',type_version:1,content:{text:'Hypothesis'},origin_kind:'ai',validation_state:'proposed',validated_by:null,validated_at:null,current_revision_id:null,is_current_confirmed:false,based_on_revision_id:null,created_at:'2026-10-17T12:00:00Z',temporal:{fact_from:null,fact_to:null,valid_from:null,valid_to:null},relation:null,provenance:[{source_id:id,source_revision_id:id,revision_no:1,origin:{kind:'synthetic'}}]};
test('open descriptors preserve spelling, case and meaningful whitespace',()=>{
 expect(descriptorValues('decision\nNew meaning\n padded \n\nDecision')).toEqual(['decision','New meaning',' padded ','Decision']);
});
test('only recognized QH-8 locators referencing returned sources become quote displays',()=>{
 const citation={source_revision_id:id,start:0,end:1,quote:'🌱'};
 expect(recognizedCitations({...row,content:{citations:[citation]}})).toEqual([]);
 const content={extraction:{key:'test',input_sha256:'abc'},citations:[citation]};
 expect(recognizedCitations({...row,content})).toEqual([citation]);
 expect(recognizedCitations({...row,content:{...content,citations:'bibliography'}})).toEqual([]);
 expect(recognizedCitations({...row,provenance:[],content})).toEqual([]);
});
test('transport rejects foreign scopes, mismatched views and malformed revision payloads',()=>{
 const q={context_ids:[id],view:'proposed' as const,limit:20};
 const page={view:'proposed',items:[row],next_after_revision_id:null};
 expect(revisionPage(page,q)).toEqual(page);
 for(const bad of [{...page,view:'history'},{...page,items:[{...row,context_space_id:'foreign'}]},{...page,items:[row,row]},{...page,items:[{...row,validation_state:'confirmed'}]}]) expect(()=>revisionPage(bad,q)).toThrow();
 expect(()=>revisionPage({view:'current',items:[row],next_after_revision_id:null},{...q,view:'current'})).toThrow();
});
test('query sends explicit view and selector with canonical cursor, without inference or owner fields',async()=>{
 const original=globalThis.fetch;let body:unknown;
 globalThis.fetch=async(path,init)=>{expect(path).toBe('/api/context-spaces/query');body=JSON.parse(String(init?.body));return new Response(JSON.stringify({view:'history',items:[row],next_after_revision_id:null}));};
 try {const query={context_ids:[id],view:'history' as const,descriptors:['new_meaning'],include_tentative:false,limit:5,after_revision_id:id};expect((await new QhApi(()=> 'synthetic-test-only',()=>{}).query(query)).items[0].revision_id).toBe(id);expect(body).toEqual(query);}finally{globalThis.fetch=original;}
});

test('historical opaque assignment JSON is not coerced into a certainty string',()=>{
 expect(descriptorAssignment({value:'new',certainty:'tentative'})).toEqual({value:'new',certainty:'tentative'});
 const opaque:Json[]=[{value:'opaque',certainty:{toString:null}},'decision',{value:'new'},null];
 for(const value of opaque) expect(descriptorAssignment(value)).toBeNull();
});

test('browse uses a scoped GET without a fabricated selector or owner field',async()=>{
 const original=globalThis.fetch;let observed='';
 globalThis.fetch=async(path,init)=>{observed=String(path);expect(init?.method).toBe('GET');expect(init?.body).toBeUndefined();return new Response(JSON.stringify({view:'history',items:[row],next_after_revision_id:null}));};
 try {await new QhApi(()=> 'synthetic-test-only',()=>{}).browse(id,{view:'history',limit:5,descriptor:' padded Ω ',include_tentative:true});const u=new URL(observed,'http://localhost');expect(u.pathname).toBe('/api/context-spaces/'+id+'/understanding');expect(u.searchParams.get('descriptor')).toBe(' padded Ω ');expect(u.searchParams.has('text')).toBe(false);expect(u.searchParams.has('owner_id')).toBe(false);}finally{globalThis.fetch=original;}
});
