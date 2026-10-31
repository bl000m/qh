export default function Loading({label,overlay=false}:{label:string;overlay?:boolean}){
 return <div className={overlay?'loading-overlay':'content-loading'} role="status"><span className="loading-spinner" aria-hidden="true"/><span className="sr-only">{label}</span></div>;
}
