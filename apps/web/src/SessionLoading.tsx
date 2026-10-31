import logo from './brand/qh-logo.png';
import './session-loading.css';

export default function SessionLoading() {
  return <div className="qh-session-loading" role="status" aria-label="Connexion à QH en cours">
    <div className="qh-session-mark" aria-hidden="true"><span className="qh-session-ring"/><img className="qh-session-logo" src={logo} width={876} height={768} alt=""/></div>
  </div>;
}

export function SessionFailure({expired = false, message, retry}: {expired?: boolean; message?: string; retry: () => void}) {
  return <main className="qh-session-failure"><div>
    <p role="alert">{message || (expired ? 'Ta session a expiré. Reconnecte-toi pour continuer.' : 'La connexion à QH n’a pas abouti. Réessaie de te connecter.')}</p>
    <button onClick={retry}>{message ? 'Réessayer' : 'Se reconnecter'}</button>
  </div></main>;
}
