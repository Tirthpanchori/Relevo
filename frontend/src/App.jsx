import { lazy, Suspense } from 'react';
import { Header, Footer, PageBoundary } from './components/Surface.jsx';
import { currentPage } from './lib/links';
import { Missing } from './pages/Reading.jsx';

const pages = {
  home: lazy(() => import('./pages/Home')),
  engine: lazy(() => import('./pages/Engine')),
  results: lazy(() => import('./pages/Results')),
  docs: lazy(() => import('./pages/Docs')),
  about: lazy(() => import('./pages/About')),
  privacy: lazy(() => import('./pages/Privacy')),
};
export default function App() {
  const current = currentPage();
  const Page = pages[current];
  return <><div id="top"/><a className="skip" href="#main">Skip to content</a><Header current={current}/><Suspense fallback={<main id="main" className="reading-page"><p role="status">Opening Relevo…</p></main>}>
    <PageBoundary>{Page ? <Page/> : <Missing/>}</PageBoundary><Footer reveal={current==='home'}/>
  </Suspense></>;
}
