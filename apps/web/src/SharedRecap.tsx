import type {SharedPayload} from '@qh/shared';
export default function SharedRecap({recap}:{recap:SharedPayload['recap']}){
 if(!recap)return null;
 return <><h3>{recap.title}</h3>{recap.text.split(/\n\s*\n/).map((text,index)=><p className="context-recap" key={index}>{text}</p>)}</>;
}
