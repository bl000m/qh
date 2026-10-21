import {useEffect,useRef,useState,useSyncExternalStore} from 'react';
import type {BrowserSession} from './auth';
import {drafts} from './drafts';
import {Icon,Orb} from './Ui';
export default function SessionExpired({session}:{session:BrowserSession}){
 const dialog=useRef<HTMLDialogElement>(null),value=useSyncExternalStore(drafts.subscribe,drafts.snapshot);
 const [notice,setNotice]=useState('');
 useEffect(()=>{dialog.current?.showModal();return()=>dialog.current?.close();},[]);
 return <dialog ref={dialog} className="session-expired" onCancel={e=>e.preventDefault()} aria-labelledby="expired-title" aria-describedby="expired-description">
  <Orb/><h2 id="expired-title">Session expirée</h2><p id="expired-description">Je me reconnecte pour continuer.</p>
  <div className="expired-drafts">{(['message','element'] as const).map((kind,i)=><div className="expired-draft" key={kind}><span className="card-icon"><Icon name={i===0?'discussion':'sources'}/></span><span><strong>{i===0?'Message en cours':'Élément en cours'}</strong><small>{value[kind]?'Conservé sur cet appareil':'Aucun brouillon en cours'}</small></span></div>)}</div>
  <p className="expired-restore"><Icon name="clock"/>Vos brouillons seront restaurés après reconnexion au même compte et au même Space, pendant 30 minutes.</p>
  <button className="expired-reconnect" onClick={()=>{if(drafts.suspend()){void session.login();}else setNotice('Le stockage temporaire est indisponible. Copiez votre brouillon avant de continuer.');}}>Me reconnecter</button>
  <button className="secondary expired-copy" onClick={()=>{const text=[value.message,value.element].filter(Boolean).join('\n\n');void navigator.clipboard.writeText(text).then(()=>setNotice('Brouillon copié.'),()=>setNotice('Copie indisponible. Votre texte reste dans cet onglet.'));}} disabled={!value.message&&!value.element}><Icon name="copy"/>Copier mon brouillon</button>
  <button className="text-button expired-clear" onClick={()=>{drafts.clear();setNotice('Brouillons effacés.');}}>Effacer les brouillons</button>
  {notice&&<p role="status" className="small">{notice}</p>}
 </dialog>;
}
