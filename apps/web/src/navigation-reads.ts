// Per QhApi/session only: deduplicate pending reads, retain at most four
// prefetched workspaces briefly. Failed and invalidated reads are never retained.
export class NavigationReads {
 private entries=new Map<string,{promise:Promise<unknown>;expires:number}>();
 read<T>(key:string,load:()=>Promise<T>,retainMs=0):Promise<T>{
  const previous=this.entries.get(key);
  if(previous&&previous.expires>Date.now())return previous.promise as Promise<T>;
  const entry={promise:Promise.resolve().then(load),expires:Infinity};
  this.entries.set(key,entry);
  entry.promise.then(()=>{
   if(this.entries.get(key)!==entry)return;
   if(!retainMs){this.entries.delete(key);return;}
   entry.expires=Date.now()+retainMs;
   const completed=[...this.entries].filter(([,value])=>Number.isFinite(value.expires));
   for(const [old] of completed.slice(0,-4))this.entries.delete(old);
  },()=>{if(this.entries.get(key)===entry)this.entries.delete(key);});
  return entry.promise;
 }
 clear(){this.entries.clear();}
 remove(key:string){this.entries.delete(key);}
 removePrefix(prefix:string){for(const key of this.entries.keys())if(key.startsWith(prefix))this.entries.delete(key);}
}
