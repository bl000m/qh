import {ApiError,isUuid} from './transport';
export interface Domain {id:string;name:string;description?:string}
export interface Organization {version:number;space_descriptions?:Record<string,string>;domains:Domain[];memberships:Record<string,string[]>;primary_domains:Record<string,string>;usage:Record<string,{last_opened_at:string;open_count:number}>}
export function organization(raw:unknown):Organization{
 const d=raw as Organization;
 if(!d||!Number.isSafeInteger(d.version)||d.version<0||!Array.isArray(d.domains)||d.domains.length>50||!d.memberships||typeof d.memberships!=='object'||Array.isArray(d.memberships)||Object.keys(d.memberships).length>1000)throw new ApiError(502);
 const ids=new Set<string>();
 for(const domain of d.domains){if(!domain||!isUuid(domain.id)||ids.has(domain.id)||typeof domain.name!=='string'||!domain.name.trim()||[...domain.name].length>100)throw new ApiError(502);ids.add(domain.id);}
 for(const [space,values] of Object.entries(d.memberships))if(!isUuid(space)||!Array.isArray(values)||values.some(v=>!ids.has(v))||new Set(values).size!==values.length)throw new ApiError(502);
 if(!d.primary_domains||!d.usage||Array.isArray(d.primary_domains)||Array.isArray(d.usage))throw new ApiError(502);
 for(const [space,values] of Object.entries(d.memberships))if(values.length&&!values.includes(d.primary_domains[space]))throw new ApiError(502);
 for(const [space,value] of Object.entries(d.usage))if(!isUuid(space)||!value||!Number.isFinite(Date.parse(value.last_opened_at))||!Number.isSafeInteger(value.open_count)||value.open_count<1)throw new ApiError(502);
 if(d.space_descriptions!==undefined&&(d.space_descriptions===null||typeof d.space_descriptions!=='object'||Array.isArray(d.space_descriptions)||Object.keys(d.space_descriptions).length>1000||Object.keys(d.space_descriptions).some(id=>!isUuid(id))))throw new ApiError(502);
 for(const description of [...d.domains.map(v=>v.description===undefined?'':v.description),...Object.values(d.space_descriptions??{})])if(typeof description!=='string'||[...description].length>500||description.includes('\0'))throw new ApiError(502);
 return d;
}
