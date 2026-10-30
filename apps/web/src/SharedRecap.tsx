import type {SharedPayload} from '@qh/shared';
export default function SharedRecap({recap,documentRecaps=[]}:{recap?:SharedPayload['recap']|null;documentRecaps?:SharedPayload['document_recaps']}){
 return <>{[...(recap?[recap]:[]),...documentRecaps].map((component,index)=><section className="shared-recap-component" key={index}><h3>{component.title}</h3>{component.text.split(/\n\s*\n/).map((text,i)=><p className="context-recap" key={i}>{text}</p>)}</section>)}</>;
}
