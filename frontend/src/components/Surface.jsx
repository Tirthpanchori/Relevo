import { Component, useEffect, useRef, useState } from 'react';
import ScrollReveal from './ScrollReveal.jsx';
import { motion, useReducedMotion } from 'motion/react';
import { asset, page } from '../lib/links.js';
export function Link({href,...props}){return <a {...props} href={typeof href === 'string' && href.startsWith('/') ? page(href.slice(1)) : href}/>;}

export const repository = 'https://github.com/Tirthpanchori/Relevo';
export const source = path => `${repository}/blob/main/${path}`;
export const Arrow = ({ back = false }) => <svg className={back ? 'arrow back' : 'arrow'} viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M4 12h15m-6-6 6 6-6 6" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round"/></svg>;
export function Glyph({ name }) { return <svg className="glyph" viewBox="0 0 24 24" fill="none" aria-hidden="true">{name === 'play' ? <path d="m9 5 10 7-10 7z" fill="currentColor"/> : name === 'pause' ? <path d="M8 5v14M16 5v14" stroke="currentColor" strokeWidth="3"/> : name === 'check' ? <path d="m5 12 4 4L19 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/> : <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>}</svg>; }
export function Action({ href, children, quiet = false }) { return <Link className={quiet ? 'text-action' : 'action'} href={href}><span className="action-label">{children}</span><Arrow/></Link>; }
export function Wordmark(){return <span className="wordmark"><span className="wordmark-name" data-wordmark="Relevo">Relevo</span><span className="brand-dot" aria-hidden="true"/></span>;}
export function Header({ current }) {
 const [scrolled,setScrolled]=useState(false);
 useEffect(()=>{const update=()=>setScrolled(window.scrollY>12);update();window.addEventListener('scroll',update,{passive:true});return()=>window.removeEventListener('scroll',update);},[]);
 return <header className="header" data-scrolled={scrolled}><Link className="brand" href="/" aria-label="Relevo home"><Wordmark/></Link><nav aria-label="Main navigation">{[['','Home'],['engine','Engine'],['results','Results'],['docs','Docs']].map(([slug,label]) => <Link key={label} href={`/${slug}${slug ? '/' : ''}`} aria-current={(current === 'home' ? '' : current) === slug ? 'page' : undefined}>{label}</Link>)}</nav></header>;
}
export function Footer({reveal=false}) {
 const groups = [['Explore',[['Home','/'],['Engine','/engine/'],['Results','/results/']]],['Build',[['Quickstart','/docs/#quickstart'],['How it works','/docs/#concepts'],['API reference','/docs/#api']]],['Project',[['About','/about/'],['Privacy','/privacy/'],['GitHub',repository]]],['Index',[['llms.txt','/llms.txt'],['Sitemap','/sitemap.xml']]]];
 return <footer className="footer"><ScrollReveal name="footer" enabled={reveal} className="footer-top"><div><Link className="brand" href="/" aria-label="Relevo home"><Wordmark/></Link><p>The worker can change.<br/>The work stays accounted for.</p></div>{groups.map(([label,links]) => <nav key={label} aria-label={`${label} footer`}><h2>{label}</h2>{links.map(([text,href]) => <Link href={href} key={text}>{text}</Link>)}</nav>)}</ScrollReveal><div className="footer-word" aria-hidden="true"><Wordmark/></div><div className="footer-bottom"><span>Built by Tirth Panchori · {new Date().getFullYear()}</span><span>Saved work. Clear history.</span><Link href="#top">Back to top<Arrow/></Link></div></footer>;
}
export function Intro({ title, children, className = '' }) { return <section className={`intro ${className}`}><h1>{title}</h1><p>{children}</p></section>; }
export function Technical({ children, title = 'Technical details' }) { return <details className="technical"><summary>{title}<Glyph/></summary><div className="technical-content">{children}</div></details>; }
export function FAQ({ items }) {
 const [open,setOpen] = useState(null), calm = useReducedMotion();
 return <div className="faq-list">{items.map(([question,answer],i) => <section className={`faq-row ${open === i ? 'open' : ''}`} key={question}><h3><button aria-expanded={open === i} aria-controls={`answer-${i}`} onClick={() => setOpen(open === i ? null : i)}>{question}<span className="plus" aria-hidden="true"/></button></h3><motion.div id={`answer-${i}`} role="region" aria-label={question} inert={open === i ? undefined : true} initial={false} animate={{ height: open === i ? 'auto' : 0, opacity: open === i ? 1 : 0 }} transition={{ duration: calm ? 0 : .34, ease: [.16,1,.3,1] }} style={{overflow:'hidden'}}><p>{answer}</p></motion.div></section>)}</div>;
}
export function useEvidence(file, validate = value => value) {
 const [state,setState] = useState({data:null,error:false}), [version,setVersion] = useState(0);
 const validator = useRef(validate); validator.current = validate;
 useEffect(() => {
  const controller = new AbortController(); setState({data:null,error:false});
  fetch(asset(`evidence/${file}`), {signal:controller.signal}).then(response => {if (!response.ok) throw Error('Unavailable'); return response.json();}).then(data => { validator.current(data); if (!controller.signal.aborted) setState({data,error:false}); }).catch(error => {if(error.name !== 'AbortError' && !controller.signal.aborted) setState({data:null,error:true});});
  return () => controller.abort();
 },[file,version]);
 return {...state,retry:() => setVersion(value => value + 1)};
}
export function Loading({ resource, children }) {
 if (resource.error) return <div className="evidence-state" role="alert"><h2>The evidence couldn’t load.</h2><p>Your place is safe. Try fetching the local recording again.</p><button className="action" onClick={resource.retry}>Try again<Arrow/></button></div>;
 if (!resource.data) return <div className="evidence-state" role="status">Loading the evidence…</div>;
 return children;
}
export class PageBoundary extends Component {
 state = {error:false};
 static getDerivedStateFromError() {return {error:true};}
 render() {return this.state.error ? <main id="main" className="reading-page"><h1>Something interrupted this page.</h1><p>Reload the preview to try again.</p><button className="action" onClick={() => location.reload()}>Reload<Arrow/></button></main> : this.props.children;}
}
export function Code({ children, language = 'Terminal' }) {
 const [message,setMessage] = useState('Copy'), timer = useRef();
 useEffect(() => () => clearTimeout(timer.current),[]);
 async function copy() {try {await navigator.clipboard.writeText(children);setMessage('Copied');} catch {setMessage('Select to copy');} clearTimeout(timer.current);timer.current=setTimeout(()=>setMessage('Copy'),1800);}
 return <div className="code"><div><span>{language}</span><button onClick={copy} aria-label={`Copy ${language.toLowerCase()} commands`}>{message}</button></div><pre tabIndex={0} aria-label={`${language} commands, horizontally scrollable`}><code>{children}</code></pre></div>;
}
