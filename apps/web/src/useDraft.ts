import {useSyncExternalStore} from 'react';
import {drafts} from './drafts';
import type {Drafts} from './drafts';
export default function useDraft(kind:keyof Drafts):[string,(text:string)=>void]{
 const value=useSyncExternalStore(drafts.subscribe,drafts.snapshot);
 return [value[kind],text=>drafts.update(kind,text)];
}
