// Unsent text only. No credentials, conversation history or canonical writes.
export type Drafts = Readonly<{message:string;element:string}>;
type StoragePort = Pick<Storage,'getItem'|'setItem'|'removeItem'>;
const EMPTY:Drafts=Object.freeze({message:'',element:''});
const KEY='qh.unsent-drafts.v1',MAX_AGE=30*60*1000;
const uuid=/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
export function createDrafts(storage:()=>StoragePort,now:()=>number=Date.now){
 let owner='',scope='',value=EMPTY;
 const listeners=new Set<()=>void>();
 function emit(next:Drafts){value=next;listeners.forEach(fn=>fn());}
 function remove(){try{storage().removeItem(KEY);}catch{/* Storage may be disabled. */}}
 function clear(){remove();emit(EMPTY);}
 function read():{owner:string;scope:string;message:string;element:string;savedAt:number}|null{
  try{
   const raw=storage().getItem(KEY);if(!raw)return null;
   if(raw.length>18000)throw Error();
   const data:unknown=JSON.parse(raw);
   if(!data||typeof data!=='object'||Array.isArray(data))throw Error();
   const d=data as Record<string,unknown>;
   if(Object.keys(d).sort().join(',')!=='element,message,owner,savedAt,scope,version'||d.version!==1||typeof d.owner!=='string'||!uuid.test(d.owner)||typeof d.scope!=='string'||!uuid.test(d.scope)||typeof d.message!=='string'||d.message.length>4096||typeof d.element!=='string'||d.element.length>4096||typeof d.savedAt!=='number'||!Number.isFinite(d.savedAt)||d.savedAt>now()||now()-d.savedAt>=MAX_AGE)throw Error();
   return {owner:d.owner,scope:d.scope,message:d.message,element:d.element,savedAt:d.savedAt};
  }catch{remove();return null;}
 }
 return {
  subscribe:(fn:()=>void)=>{listeners.add(fn);return()=>{listeners.delete(fn);};},
  snapshot:()=>value,
  verifyOwner(id:string){const pending=read();if(owner&&id!==owner||pending&&pending.owner!==id)clear();owner=id;},
  // Called only after authenticated QH identity AND owned Space GET succeeded.
  enter(id:string,space:string){
   if(!uuid.test(id)||!uuid.test(space)){owner='';scope='';clear();return;}
   if(owner!==id||scope&&scope!==space)emit(EMPTY);
   owner=id;scope=space;
   const pending=read();
   if(pending){remove();if(pending.owner===id&&pending.scope===space)emit({message:pending.message,element:pending.element});}
  },
  update(kind:keyof Drafts,text:string){if(owner&&scope)emit({...value,[kind]:text.slice(0,4096)});},
  clear,
  logout(){owner='';scope='';clear();},
  suspend(){
   remove();
   if(!uuid.test(owner)||!uuid.test(scope))return false;
   if(!value.message&&!value.element)return true;
   try{storage().setItem(KEY,JSON.stringify({version:1,owner,scope,...value,savedAt:now()}));return true;}catch{remove();return false;}
  }
 };
}
export const drafts=createDrafts(()=>window.sessionStorage);
