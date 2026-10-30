import type {SharedPayload} from '@qh/shared';
export default function SharedRecap({recap}:{recap?:SharedPayload['recap']|null}){
 return recap?<section className="shared-recap-component"><h3>{recap.title}</h3>{recap.text.split(/\n\s*\n/).map((text,i)=><p className="context-recap" key={i}>{text}</p>)}</section>:null;
}
