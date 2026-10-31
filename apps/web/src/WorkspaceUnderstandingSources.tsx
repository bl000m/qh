import type {CanonicalRevision, Citation, SourceRevision} from './understanding';
import {recognizedCitations,sourceCitationLabel} from './understanding';

function groupSources(rows:CanonicalRevision[]){
 const groups=new Map<string,{source:SourceRevision;passages:Citation[];items:{row:CanonicalRevision;passages:number[]}[]}>();
 for(const row of rows){
  const citations=recognizedCitations(row);
  for(const source of row.provenance){
   let group=groups.get(source.source_revision_id);
   if(!group){group={source,passages:[],items:[]};groups.set(source.source_revision_id,group);}
   const passages=citations.filter(c=>c.source_revision_id===source.source_revision_id).map(citation=>{
    let index=group.passages.findIndex(p=>p.start===citation.start&&p.end===citation.end&&p.turn_id===citation.turn_id&&p.quote===citation.quote);
    if(index<0){index=group.passages.length;group.passages.push(citation);}
    return index+1;
   });
   group.items.push({row,passages:[...new Set(passages)]});
  }
 }
 return [...groups.values()];
}

export default function WorkspaceUnderstandingSources({rows}:{rows:CanonicalRevision[]}){
 return <>{groupSources(rows).map(({source,passages,items},index)=><section key={source.source_revision_id} aria-label={`Source ${index+1}`}>
  <h4>Source {index+1} · révision {source.revision_no}</h4>
  {passages.map((citation,i)=><div key={i}>
   <p className="small muted">{sourceCitationLabel(source,citation)??`Passage ${i+1}`}</p><blockquote>{citation.quote}</blockquote>
   <details><summary>Référence précise</summary><p className="small">Source : {citation.source_revision_id} · caractères {citation.start}–{citation.end}{citation.turn_id&&` · tour ${citation.turn_id}`}</p></details>
  </div>)}
  <h5>Éléments de compréhension liés ({items.length})</h5>
  <ul>{items.map(({row,passages:refs})=><li key={row.revision_id}>
   <p>{String(row.content.text??'')}</p><p className="small muted">{row.validation_state==='confirmed'?'Confirmé':row.validation_state==='rejected'?'Rejeté':'Proposé'}{refs.length>0&&` · passages ${refs.join(', ')}`}</p>
  </li>)}</ul>
 </section>)}</>;
}
