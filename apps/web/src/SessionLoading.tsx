import {useId} from 'react';
import logo from './brand/qh-logo.png';
import './session-loading.css';

export default function SessionLoading() {
  const mask = useId();
  return <div className="qh-session-loading" role="status" aria-label="Connexion à QH en cours">
    <svg className="qh-session-symbol" viewBox="0 0 768 768" aria-hidden="true">
      <defs><filter id={mask} colorInterpolationFilters="sRGB">
        <feColorMatrix in="SourceGraphic" type="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  3 -3 0 0 0" result="red"/>
        <feComposite in="SourceGraphic" in2="red" operator="in"/>
      </filter></defs>
      {/* Select existing red pixels without modifying the PNG or recreating hidden artwork. */}
      <image href={logo} width="876" height="768" filter={`url(#${mask})`}/>
    </svg>
  </div>;
}

export function SessionFailure({expired = false, retry}: {expired?: boolean; retry: () => void}) {
  return <main className="qh-session-failure"><div>
    <p role="alert">{expired ? 'Ta session a expiré. Reconnecte-toi pour continuer.' : 'La connexion à QH n’a pas abouti. Réessaie de te connecter.'}</p>
    <button onClick={retry}>Se reconnecter</button>
  </div></main>;
}
