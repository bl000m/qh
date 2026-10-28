import {useEffect, useMemo, useRef, useState} from 'react';
import type {CSSProperties, RefObject} from 'react';
import type {useOrganization} from './EnvironmentDomains';
import {AddDomain} from './EnvironmentDomains';
import {domainBubbles} from './environment-bubbles';
import type {BubbleLabel} from './environment-bubbles';
import Link from './NavLink';
import {domainPath} from './navigation';
import Loading from './Loading';
import bubble from './brand/qh-environment-bubble.png';
import './environment-home.css';

export default function EnvironmentHome({state, headingRef}: {state: ReturnType<typeof useOrganization>; headingRef: RefObject<HTMLHeadingElement>}) {
  const [adding, setAdding] = useState(false);
  const [scrollable, setScrollable] = useState(false);
  const viewport = useRef<HTMLDivElement>(null);
  const [measurements, setMeasurements] = useState<{diameter: number; labels: Record<string, BubbleLabel>}>({diameter: 1, labels: {}});
  const initialBubbles = useMemo(() => state.value ? domainBubbles(state.value) : [], [state.value]);
  const bubbles = useMemo(() => state.value ? domainBubbles(state.value, measurements.labels, measurements.diameter) : [], [state.value, measurements]);
  const labelSizes = Object.values(measurements.labels);
  const minimumDiameter = Math.ceil(Math.max(initialBubbles.length ? 64 / Math.min(...initialBubbles.map(item => item.radius)) : 0,
    ...labelSizes.map(label => label.width * 1.1), 1.4 * Math.sqrt(labelSizes.reduce((area, label) => area + label.width * label.height, 0))));
  useEffect(() => {
    const node = viewport.current;
    if (!node) return;
    const measure = () => {
      const sphere = node.querySelector<HTMLElement>('.environment-sphere')!;
      const labels = Object.fromEntries([...node.querySelectorAll<HTMLElement>('.environment-domain')].map(domain => {
        const text = domain.querySelector<HTMLElement>('.environment-domain-text')!;
        return [domain.dataset.domainId!, {width: text.offsetWidth, height: text.offsetHeight}];
      }));
      setScrollable(sphere.offsetWidth > node.clientWidth + 1);
      setMeasurements(previous => previous.diameter === sphere.offsetWidth && JSON.stringify(previous.labels) === JSON.stringify(labels) ? previous : {diameter: sphere.offsetWidth, labels});
    };
    measure();
    const observer = new ResizeObserver(measure);
    observer.observe(node);
    return () => observer.disconnect();
  }, [minimumDiameter, state.value]);
  return <section className="environment-home-visual" aria-labelledby="environment-title" style={{'--environment-minimum-diameter': `${minimumDiameter}px`} as CSSProperties}>
    <div className="environment-introduction"><h1 id="environment-title" ref={headingRef} tabIndex={-1}>Mon environnement</h1>
      <p>Tes domaines regroupent des Context Spaces autour d'un même thème. Ton environnement est un espace vivant qui évolue avec toi.</p>
    </div>
    {state.error && <div className="environment-error" role="alert"><p>{state.error}</p><button className="secondary" onClick={state.reload}>Recharger l’organisation</button></div>}
    <div className="environment-stage">
      <div ref={viewport} className={'environment-window' + (scrollable ? ' is-scrollable' : '')} tabIndex={scrollable ? 0 : undefined} role="region" aria-label="Domaines de mon environnement" aria-describedby={scrollable ? 'environment-scroll-help' : undefined}><div className="environment-sphere">
        <img className="environment-bubble-art" src={bubble} width={1261} height={1247} alt="" aria-hidden="true"/>
        {!state.value && !state.error && <div className="environment-empty"><Loading label="Chargement de ton organisation…"/></div>}
        {state.value && !bubbles.length && <p className="environment-empty">Ton environnement attend son premier domaine.<br/>Ajoute un domaine pour commencer.</p>}
        <ul className="environment-domains" aria-label="Mes domaines">{bubbles.map(({domain, count, x, y, radius}, index) =>
          <li key={domain.id} data-domain-id={domain.id} className="environment-domain" style={{left: `${(x + 1 - radius) * 50}%`, top: `${(y + 1 - radius) * 50}%`, width: `${radius * 100}%`, '--float-duration': `${5.5 + index % 5}s`, '--float-delay': `${-index * 1.3}s`, '--float-direction': index % 2 ? 'reverse' : 'normal'} as CSSProperties}>
            <Link to={domainPath(domain.id)} className="environment-domain-link" label={`${domain.name} — ${count} Context Space${count > 1 ? 's' : ''}`} title={domain.name}>
              <img className="environment-bubble-art" src={bubble} width={1261} height={1247} alt="" aria-hidden="true"/>
              <span className="environment-domain-text"><span className="environment-domain-label"><span aria-hidden="true">&gt;</span><span>{domain.name}</span></span><span className="environment-domain-count">{count} espace{count > 1 ? 's' : ''}</span></span>
            </Link>
          </li>)}</ul>
      </div></div>
      <button className="environment-add" disabled={!state.value || state.busy || state.value.domains.length >= 50} title={state.value?.domains.length === 50 ? 'La limite de 50 domaines est atteinte.' : undefined} onClick={() => setAdding(true)}><span aria-hidden="true">+</span><span>Ajouter un domaine</span></button>
    </div>
    {scrollable && <p id="environment-scroll-help" className="environment-scroll-hint">Fais défiler la bulle pour explorer tous tes domaines.</p>}
    {adding && <AddDomain state={state} onClose={() => setAdding(false)}/>}
  </section>;
}
