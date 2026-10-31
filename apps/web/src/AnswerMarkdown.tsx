import type {ReactNode} from 'react';

// A deliberately small renderer: React escapes every text node; no HTML parser,
// remote images, executable URLs or provider-controlled attributes.
function inline(text:string):ReactNode[]{
 const parts:ReactNode[]=[],pattern=/(`[^`\n]+`|\*\*[^*\n]+\*\*|__[^_\n]+__|\*[^*\n]+\*|_[^_\n]+_|\[[^\[\]\n]+\]\([^\s)]+\))/g;let at=0;
 for(const match of text.matchAll(pattern)){
  parts.push(text.slice(at,match.index));const value=match[0],key=match.index;
  if(value.startsWith('`'))parts.push(<code key={key}>{value.slice(1,-1)}</code>);
  else if(value.startsWith('**')||value.startsWith('__'))parts.push(<strong key={key}>{value.slice(2,-2)}</strong>);
  else if(value.startsWith('*')||value.startsWith('_'))parts.push(<em key={key}>{value.slice(1,-1)}</em>);
  else{const split=value.indexOf(']('),href=value.slice(split+2,-1);let safe=false;try{safe=['https:','http:','mailto:'].includes(new URL(href).protocol);}catch{/* Render unsupported links as text. */}parts.push(safe?<a key={key} href={href} target="_blank" rel="noopener noreferrer">{value.slice(1,split)}</a>:value);}
  at=match.index+value.length;
 }
 parts.push(text.slice(at));return parts;
}
export default function AnswerMarkdown({text}:{text:string}){
 const blocks:ReactNode[]=[],lines=text.split(/\r?\n/);let paragraph:string[]=[],items:string[]=[],ordered=false,start=1,next=1;
 // Numbering continues across lists separated only by nested bullets or blank lines;
 // a paragraph or heading starts a new sequence.
 function flush(){
  if(paragraph.length){blocks.push(<p key={blocks.length}>{paragraph.map((line,i)=><span key={i}>{i>0&&<br/>}{inline(line)}</span>)}</p>);paragraph=[];next=1;}
  if(items.length){const rows=items.map((line,i)=><li key={i}>{inline(line)}</li>);
   blocks.push(ordered?<ol key={blocks.length} start={start}>{rows}</ol>:<ul key={blocks.length}>{rows}</ul>);
   if(ordered)next=start+items.length;items=[];}
 }
 for(const line of lines){const list=/^\s*([-+*]|(\d+)\.)\s+(.+)$/.exec(line),heading=/^#{1,3}\s+(.+)$/.exec(line);
  if(!line.trim()){flush();continue;}
  if(heading){flush();next=1;blocks.push(<h4 key={blocks.length}>{inline(heading[1])}</h4>);continue;}
  if(list){const numbered=list[2]!==undefined;if(paragraph.length||items.length&&ordered!==numbered)flush();
   if(numbered&&!items.length)start=Math.max(next,parseInt(list[2],10));ordered=numbered;items.push(list[3]);}
  else{if(items.length)flush();paragraph.push(line);}
 }
 flush();return <div className="chat-text chat-markdown">{blocks}</div>;
}
