import {ApiError,isUuid} from './transport';
export interface Domain {id:string;name:string}
export interface Organization {version:number;domains:Domain[];memberships:Record<string,string[]>}
export function organization(raw:unknown):Organization{
 const d=raw as Organization;
 if(!d||!Number.isSafeInteger(d.version)||d.version<0||!Array.isArray(d.domains)||d.domains.length>50||!d.memberships||typeof d.memberships!=='object'||Array.isArray(d.memberships)||Object.keys(d.memberships).length>1000)throw new ApiError(502);
 const ids=new Set<string>();
 for(const domain of d.domains){if(!domain||!isUuid(domain.id)||ids.has(domain.id)||typeof domain.name!=='string'||!domain.name.trim()||[...domain.name].length>100)throw new ApiError(502);ids.add(domain.id);}
 for(const [space,values] of Object.entries(d.memberships))if(!isUuid(space)||!Array.isArray(values)||values.some(v=>!ids.has(v))||new Set(values).size!==values.length)throw new ApiError(502);
 return d;
}
