import {useEffect, useMemo, useRef, useState} from 'react';
import type {CSSProperties, RefObject} from 'react';
import type {useOrganization} from './EnvironmentDomains';
import {AddDomain} from './EnvironmentDomains';
import {domainBubbles, domainDisplayNames, domainHoverScale} from './environment-bubbles';
import type {BubbleLabel, ReservedArea} from './environment-bubbles';
import Link from './NavLink';
import {domainPath} from './navigation';
import Loading from './Loading';
import bubble from './brand/qh-environment-bubble.png';
import './environment-home.css';

export default function EnvironmentHome({state, headingRef}: {state: ReturnType<typeof useOrganization>; headingRef: RefObject<HTMLHeadingElement>}) {
  const [adding, setAdding] = useState(false);
  const viewport = useRef<HTMLDivElement>(null);
  const displayNames = useMemo(() => domainDisplayNames(state.value?.domains ?? []), [state.value]);
  const [measurements, setMeasurements] = useState<{width: number; height: number; labels: Record<string, BubbleLabel>; reserved: ReservedArea}>({width: 800, height: 650, labels: {}, reserved: {width: 0, height: 0}});
  const bubbles = useMemo(() => state.value ? domainBubbles(state.value, measurements.labels, measurements.width, measurements.height, measurements.reserved) : [], [state.value, measurements]);
  const areaHeight = Math.max(measurements.height, ...bubbles.map(item => item.y + item.radius * 1.5 + 24));
  useEffect(() => {
    const node = viewport.current;
    if (!node) return;
    const measure = () => {
      const labels = Object.fromEntries([...node.querySelectorAll<HTMLElement>('.environment-domain')].map(domain => {
        const text = domain.querySelector<HTMLElement>('.environment-domain-text')!;
        return [domain.dataset.domainId!, {width: text.offsetWidth, height: text.offsetHeight}];
      }));
      const width = node.clientWidth, height = Math.max(320, window.innerHeight - 150);
      const bounds = node.getBoundingClientRect(), intro = node.closest('.environment-home-visual')!.querySelector('.environment-introduction')!.getBoundingClientRect();
      const reserved = intro.bottom > bounds.top ? {width: intro.right - bounds.left, height: intro.bottom - bounds.top} : {width: 0, height: 0};
      const next = {width, height, labels, reserved};
      setMeasurements(previous => JSON.stringify(previous) === JSON.stringify(next) ? previous : next);
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(node);
    window.addEventListener('resize', measure);
    return () => {observer.disconnect(); window.removeEventListener('resize', measure);};
  }, [state.value]);
  return <section className="environment-home-visual" aria-labelledby="environment-title" style={{'--environment-area-height': `${areaHeight}px`} as CSSProperties}>
    <div className="environment-introduction"><h1 id="environment-title" ref={headingRef} tabIndex={-1}>Mon environnement</h1>
      <p>Tes domaines regroupent des Context Spaces autour d'un même thème. Ton environnement est un espace vivant qui évolue avec toi.</p>
    </div>
    {state.error && <div className="environment-error" role="alert"><p>{state.error}</p><button className="secondary" onClick={state.reload}>Recharger l’organisation</button></div>}
    <div className="environment-stage">
      <div ref={viewport} className="environment-window" role="region" aria-label="Domaines de mon environnement"><div className="environment-sphere">
        <img className="environment-bubble-art" src={bubble} width={1400} height={1450} alt="" aria-hidden="true"/>
        {!state.value && !state.error && <div className="environment-empty"><Loading label="Chargement de ton organisation…"/></div>}
        {state.value && !bubbles.length && <p className="environment-empty">Ton environnement attend son premier domaine.<br/>Ajoute un domaine pour commencer.</p>}
        <ul className="environment-domains" aria-label="Mes domaines">{bubbles.map(({domain, count, x, y, radius}, index) =>
          <li key={domain.id} data-domain-id={domain.id} className="environment-domain" style={{left: `${x - radius}px`, top: `${y - radius}px`, width: `${radius * 2}px`, '--hover-scale': domainHoverScale({domain, count, x, y, radius}, measurements.width, areaHeight, measurements.reserved), '--float-x': `${4 + index % 3}px`, '--float-y': `${5 + index % 4}px`, '--float-duration': `${7.5 + index % 5}s`, '--float-delay': `${-index * 1.3}s`, '--float-direction': index % 2 ? 'reverse' : 'normal'} as CSSProperties}>
            <Link to={domainPath(domain.id)} className="environment-domain-link" label={`${domain.name} — ${count} Context Space${count > 1 ? 's' : ''}`} title={domain.name}>
              <img className="environment-bubble-art" src={bubble} width={1400} height={1450} alt="" aria-hidden="true"/>
              <span className="environment-domain-text"><span className={'environment-domain-label' + (displayNames[domain.id] === domain.name ? ' environment-domain-label-full' : '')}><span aria-hidden="true">&gt;</span><span>{displayNames[domain.id]}</span></span><span className="environment-domain-count">{count} espace{count > 1 ? 's' : ''}</span></span>
            </Link>
          </li>)}</ul>
      </div></div>
      <button className="environment-add" disabled={!state.value || state.busy || state.value.domains.length >= 50} title={state.value?.domains.length === 50 ? 'La limite de 50 domaines est atteinte.' : undefined} onClick={() => setAdding(true)}><span aria-hidden="true">+</span><span>Ajouter un domaine</span></button>
    </div>
    {adding && <AddDomain state={state} onClose={() => setAdding(false)}/>}
  </section>;
}
