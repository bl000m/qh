import type {CSSProperties} from 'react';
import bubble from './brand/qh-bubble.png';
export function Orb({tone=0}:{tone?:number}){
 return <span className="orb-art" style={{'--orb-tone':tone+'deg'} as CSSProperties}><img className="qh-bubble" src={bubble} alt="" aria-hidden="true" width={400} height={300}/></span>;
}
export function Icon({name}:{name:'settings'|'link'|'trash'|'sources'|'understanding'|'info'|'logout'}){
 const paths={settings:<><path d="m9 3 1-1h4l1 3 3 1 3-1 2 4-2 2v3l2 2-2 4-3-1-3 1-1 3h-4l-1-3-3-1-3 1-2-4 2-2v-3L1 9l2-4 3 1 3-1Z"/><circle cx="12" cy="12" r="3"/></>,link:<><path d="m10 13 4-4M8 15l-2 2a4 4 0 0 1-5-5l5-5a4 4 0 0 1 5 0m2 2 2-2a4 4 0 0 1 5 5l-5 5a4 4 0 0 1-5 0"/></>,trash:<><path d="M3 6h18M9 6V3h6v3M6 6l1 15h10l1-15M10 10v7m4-7v7"/></>,sources:<><path d="M6 2h8l4 4v16H6V2Zm8 0v5h4M9 11h6m-6 4h6m-6 4h4"/></>,understanding:<><path d="m12 2 10 6-10 6L2 8l10-6Zm-10 11 10 6 10-6M2 18l10 5 10-5"/></>,info:<><circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v1"/></>,logout:<><path d="M9 3H3v18h6m5-15 6 6-6 6m6-6H8"/></>};
 return <svg className="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}
