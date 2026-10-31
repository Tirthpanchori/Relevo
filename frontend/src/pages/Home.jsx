import ScrollReveal from '../components/ScrollReveal.jsx';
import PixelField from '../components/PixelField.jsx';
import { Action, FAQ, Glyph } from '../components/Surface.jsx';
import RelayModel from '../components/RelayModel.jsx';

const faqs = [
 ['What does Relevo actually do?','It keeps track of background tasks: what needs doing, which worker is currently assigned, and what happened on each attempt. If an assignment expires, eligible work can be tried again.'],
 ['What is a worker?','A worker is a running process that asks for a task and executes its handler. Think of it as a helper behind your application, preparing work while the application answers other requests.'],
 ['Does another worker continue where the first stopped?','No. A retry starts the task handler from the beginning. Any eligible worker can claim it, including the same worker if it becomes available again.'],
 ['Can a task still fail?','Yes. Tasks have an execution limit and a limited number of attempts. Recovery also needs the database, coordinator, scheduler and workers to be available. Relevo keeps the outcome visible; it cannot promise every task will succeed.'],
 ['Can something happen twice?','Yes. A task may run more than once during recovery. Actions outside the engine, such as sending a payment, need their own protection against duplicates. Relevo rejects outdated updates to its own task record.'],
 ['Is this a live service?','This is a portfolio engineering project. The website explains the engine and replays actual saved tests. Run the backend locally with Docker to submit and inspect your own tasks.'],
];
export default function Home() {
 return <main id="main">
  <section className="home-hero">
   <PixelField/>
   <div className="hero-copy"><h1>Background work<br/>can <span className="recover-word">recover</span>.</h1><p>Relevo saves tasks, assigns them to workers, and can retry unfinished work when a worker stops responding.</p><Action href="/engine/">See how it works</Action></div>
  </section>
  <RelayModel/>
  <section className="example-section">
   <ScrollReveal name="example-copy" className="example-copy"><h2>The click is quick.<br/>The work takes longer.</h2><p>Imagine asking an app for a report. You carry on using the app while a worker prepares it in the background.</p><p>If that worker disappears, the request still matters. Relevo keeps a saved task so the work can be tried again.</p><span className="example-note">An example of a possible integration. The demo engine runs hashing, timed work, and configured failures.</span></ScrollReveal>
   <ScrollReveal name="report-scene" delay={.1}><div className="report-scene" role="img" aria-label="An illustrative report request stays saved while a stopped worker is replaced"><div className="report-sheet"><div className="sheet-top"><span>Monthly report</span><span className="paper-mark"/></div><div className="sheet-chart"><span/><span/><span/><span/><span/><span/></div><div className="sheet-line"/><div className="sheet-line short"/><div className="report-status"><i/>Request saved</div></div><div className="worker-ticket"><span className="worker-avatar"><Glyph name="check"/></span><div><strong>Another attempt</strong><span>The request stays in the queue.</span></div></div></div></ScrollReveal>
  </section>
  <section className="recovery-story">
   <ScrollReveal name="recovery-copy"><h2>A stopped worker.<br/>A task that stayed.</h2><p>In a recorded test, we stopped the first worker after it took a task. When its assignment expired, recovery made another attempt possible. A replacement finished the task.</p><p className="subtle">A recorded recovery test, not a live task running in your browser.</p></ScrollReveal>
   <ScrollReveal name="recovery-steps" delay={.1}><ol className="story-track"><li><span className="story-dot"/><div><h3>The task was saved.</h3><p>The request had a durable home.</p></div></li><li><span className="story-dot stopped"/><div><h3>The first worker stopped.</h3><p>Its temporary assignment eventually expired.</p></div></li><li><span className="story-dot complete"><Glyph name="check"/></span><div><h3>Another worker finished.</h3><p>Both attempts stayed in the history.</p></div></li></ol></ScrollReveal>
  </section>
  <section className="faq-section" id="faq">
   <ScrollReveal name="faq-heading"><h2>A few things<br/>you might ask.</h2><p>Start with the idea.<br/>The details can come later.</p></ScrollReveal>
   <ScrollReveal name="faq-questions" delay={.1}><FAQ items={faqs}/></ScrollReveal>
  </section>
  <section className="docs-ending">
   <ScrollReveal name="docs-heading"><h2>See it on<br/>your machine.</h2></ScrollReveal>
   <ScrollReveal name="docs-action" delay={.1}><p>Run the engine, submit a task, and follow what happens. The setup guide walks you through it.</p><Action href="/docs/">Start with Docs</Action></ScrollReveal>
  </section>
 </main>;
}
