import {useEffect, useRef} from 'react';
import type {BrowserSession, SessionState} from './auth';
import Link from './NavLink';
import {Icon} from './Ui';
import logo from './brand/qh-logo.png';
import sphere from './brand/qh-home-sphere.png';
import './public-pages.css';

const pages = [
  {path: '/a-propos', label: "Qu'est-ce que QH ?", title: 'Tes contextes, accessibles à toutes tes IA'},
  {path: '/securite', label: 'Sécurité', title: 'Tes informations, sous ton contrôle'},
  {path: '/tarifs', label: 'Tarifs', title: 'Simple et transparent'}
];

export function isPublicPath(path: string) {
  return path === '/accueil' || pages.some(page => page.path === path);
}

function PublicContent({path}: {path: string}) {
  if (path === '/a-propos') return <p>QH organise les informations importantes de ta vie et de tes projets dans des Context Spaces. Chaque espace construit une compréhension qui évolue avec tes échanges et les informations que tu choisis de mémoriser. Tu peux retrouver tes contextes, les utiliser avec des IA compatibles et les partager à travers des liens sécurisés, selon les autorisations définies.</p>;
  if (path === '/securite') return <ul className="public-security">
    <li>Des espaces personnels avec accès contrôlé.</li>
    <li>Un partage par lien avec des autorisations définies.</li>
    <li>La possibilité de limiter ou révoquer les accès, selon les fonctions disponibles.</li>
    <li>Une traçabilité des informations utilisées pour construire la compréhension.</li>
  </ul>;
  return <div className="public-price"><p className="public-offer">Offre envisagée</p><p className="public-price-amount">QH — 5 € / mois</p><p>Jusqu'à une limite d'utilisation à définir.</p><p className="public-price-details">Les modalités et limites définitives seront précisées avant le lancement commercial.</p></div>;
}

export default function PublicPages({path, session, state}: {path: string; session: BrowserSession; state: SessionState}) {
  const page = pages.find(page => page.path === path);
  const heading = useRef<HTMLHeadingElement>(null);
  const previousPath = useRef(path);
  const connected = state === 'authenticated' || state === 'expired' && !!session.preserveDrafts;
  useEffect(() => {
    document.title = page ? `${page.label} — QH` : 'QH — Tes contextes, sous ton contrôle';
    if (previousPath.current !== path) heading.current?.focus();
    previousPath.current = path;
    return () => { document.title = 'QH'; };
  }, [path, page]);
  return <div className="public-shell">
    <a className="skip-link" href="#public-content">Aller au contenu</a>
    <header className="public-header">
      <Link to="/accueil" label="QH — accueil" className="public-brand"><img src={logo} width={876} height={768} alt="QH"/></Link>
      <nav aria-label="Navigation publique">{pages.map(item => <Link key={item.path} to={item.path} className={item === page ? 'public-current' : undefined}>{item.label}</Link>)}</nav>
      <div className="public-account">
        {connected ? <Link to="/" className="public-environment">Mon environnement <span aria-hidden="true">↗</span></Link> : <button className="secondary" disabled={state === 'starting'} onClick={() => {void session.login();}}>Se connecter</button>}
        <div className="public-registration"><button disabled aria-describedby="registration-status">Créer un compte</button><span id="registration-status">Inscription bientôt disponible</span></div>
      </div>
    </header>
    <main id="public-content" tabIndex={-1}>
      {state === 'error' && <p className="notice error" role="alert">La connexion n’a pas abouti. Réessaie.</p>}
      {state === 'expired' && !connected && <p className="notice" role="status">Ta session a expiré. Reconnecte-toi pour continuer.</p>}
      {page ? <article className="public-information"><h1 ref={heading} tabIndex={-1}>{page.title}</h1><PublicContent path={path}/></article> : <section className="public-hero" aria-labelledby="public-title">
        <div className="public-copy"><h1 id="public-title" ref={heading} tabIndex={-1}>Marre de tout réexpliquer à chaque IA ?</h1>
          <p>QH organise et protège tes contextes, accessibles à toutes tes IA. Tu peux les partager par un simple lien sécurisé, sans dispersion. Tu gagnes du temps et gardes le contrôle !</p>
          <ul className="public-benefits"><li><Icon name="understanding"/><span>Tes idées organisées</span></li><li><Icon name="lock"/><span>Tes données protégées</span></li><li><Icon name="share"/><span>Un partage simple et sécurisé</span></li></ul>
        </div>
        <img className="public-sphere" src={sphere} width={1266} height={1243} alt="Une femme en noir et blanc dans une sphère entourée de cinq domaines : Famille, Travail, Loisirs, Santé et Formation." decoding="async"/>
      </section>}
    </main>
  </div>;
}
