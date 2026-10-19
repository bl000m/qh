import { useSyncExternalStore } from 'react';
function subscribe(listener: () => void) {
  window.addEventListener('popstate', listener);
  return () => window.removeEventListener('popstate', listener);
}
export function usePath() { return useSyncExternalStore(subscribe, () => window.location.pathname); }
export function navigate(path: string) {
  window.history.pushState(null, '', path);
  window.dispatchEvent(new PopStateEvent('popstate'));
}
// Explicit navigation origin is carried by the URL, never inferred from membership.
const uuid='[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}';
export const domainPath=(id:string)=>'/domains/'+id;
export const spacePath=(id:string,origin?:string)=>origin?domainPath(origin)+'/context-spaces/'+id:'/context-spaces/'+id;
type Route={kind:'home'}|{kind:'settings'}|{kind:'domain';id:string}|{kind:'collection';domain:null|'unclassified'}|{kind:'space';id:string;origin?:string}|{kind:'missing'};
export function parseRoute(path:string):Route{
 if(path==='/')return {kind:'home'};
 if(path==='/settings')return {kind:'settings'};
 if(path==='/spaces'||path==='/spaces/unclassified')return {kind:'collection',domain:path.endsWith('/unclassified')?'unclassified':null};
 const domain=new RegExp('^/domains/('+uuid+')(?:/context-spaces/('+uuid+'))?$','i').exec(path);
 if(domain)return domain[2]?{kind:'space',id:domain[2],origin:domain[1]}:{kind:'domain',id:domain[1]};
 const space=new RegExp('^/context-spaces/('+uuid+')$','i').exec(path);
 return space?{kind:'space',id:space[1]}:{kind:'missing'};
}
