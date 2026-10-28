import type {MouseEvent,ReactNode} from 'react';
import {navigate} from './navigation';
export default function Link({to,children,label,title,className,onIntent}:{to:string;children:ReactNode;label?:string;title?:string;className?:string;onIntent?:()=>void}){
 function follow(event:MouseEvent<HTMLAnchorElement>){if(event.button===0&&!event.metaKey&&!event.ctrlKey&&!event.shiftKey&&!event.altKey){event.preventDefault();navigate(to);}}
 return <a href={to} onClick={follow} onMouseEnter={onIntent} onFocus={onIntent} onTouchStart={onIntent} aria-label={label} title={title} className={className}>{children}</a>;
}
