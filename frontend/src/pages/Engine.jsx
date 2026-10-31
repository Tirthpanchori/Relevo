import { useEffect, useRef, useState } from 'react';
import { motion, useReducedMotion } from 'motion/react';
import { Link, Arrow, Glyph, Intro, Technical, useEvidence, Loading } from '../components/Surface.jsx';
import { validateCapture, replayFrame } from '../lib/evidence.mjs';

const normal = [
 ['Request sent','The application asks for work.','Your application sends a background task to Relevo, so the user does not have to wait for the work to finish.','Application'],
 ['Task saved','Your request has a home.','The application submits the work. Relevo saves the task before confirming it was accepted.','Saved work'],
 ['Worker assigned','Alex takes the task.','An available worker claims a temporary assignment. The task stays saved while the worker handles it.','Worker'],
 ['Work underway','The work happens in the background.','Alex runs the task handler. The application can keep responding to other requests.','Worker'],
 ['Checking in','Still working. Still assigned.','While the task runs, the worker checks in to renew its temporary assignment. There is still a separate execution time limit.','Worker'],
 ['Task completed','The result is saved.','The current worker reports success. Relevo records the outcome and preserves the attempt in the history.','Saved work'],
];
const interrupted = [
 ...normal.slice(0,4),
 ['Assignment expired','The worker stopped checking in.','Alex is no longer responding. Once its temporary assignment expires, it can no longer report a new result.','Worker'],
 ['Recovery','Make room for another try.','The recovery scheduler records the expired attempt and schedules a retry, if the task still has attempts available.','Recovery'],
 ['Another worker','Sam takes the next attempt.','After the retry becomes eligible, an available worker claims it. Sam starts the handler from the beginning.','Worker'],
 ['Task completed','A new attempt. A saved result.','Sam finishes and reports success. Relevo keeps both attempts so the recovery remains understandable.','Saved work'],
];
function Controls({ index, count, previous, next, playing, toggle, calm }) {
 return <div className="playback"><button onClick={previous} disabled={index === 0} aria-label="Previous step"><Arrow back/>Previous</button>{toggle && <button className="play-toggle" onClick={toggle} disabled={calm} title={calm?'Reduced motion is on. Use Previous and Next.':undefined}><Glyph name={playing?'pause':'play'}/>{playing?'Pause':'Play'}</button>}<button onClick={next} disabled={index === count-1} aria-label="Next step">Next<Arrow/></button></div>;
}
function Sequence({ labels, index, onSelect }) {
 return <ol className="sequence" style={{'--steps':labels.length}}>{labels.map((label,i)=><li key={`${label}-${i}`} className={`${i===index?'current':''} ${i<index?'passed':''}`}><button aria-current={i===index?'step':undefined} onClick={()=>onSelect(i)}><span>{label}</span><i aria-hidden="true"/></button></li>)}</ol>;
}
function Flow() {
 const [path,setPath]=useState('normal'),[index,setIndex]=useState(0), steps=path==='normal'?normal:interrupted;
 const step=steps[index] || steps[0];
 return <div className="engine-workspace"><div className="workspace-toolbar"><span>Follow an example task</span><div className="segmented small" role="group" aria-label="Flow path">{[['normal','Work completes'],['interrupted','Worker stops']].map(([key,label])=><button key={key} aria-pressed={path===key} onClick={()=>{setPath(key);setIndex(0);}}>{label}</button>)}</div></div><Sequence labels={steps.map(s=>s[0])} index={index} onSelect={setIndex}/><div className="flow-map" aria-label="Responsibilities in the illustrative task">{[['Application','Asks for work'],['Saved work','Keeps the task'],['Worker','Runs an attempt'],['Recovery','Makes a retry possible']].map(([label,description],i)=><div key={label} className={step[3]===label?'active':''} data-component={label.toLowerCase().replace(' ','-')}><span className="flow-symbol" aria-hidden="true">{i===0?<svg viewBox="0 0 56 56"><rect x="8" y="11" width="40" height="30" rx="4"/><path d="M8 19h40M19 47h18M28 41v6"/></svg>:i===1?<svg viewBox="0 0 56 56"><ellipse cx="28" cy="13" rx="18" ry="6"/><path d="M10 13v28c0 8 36 8 36 0V13M10 27c0 8 36 8 36 0"/></svg>:i===2?<svg viewBox="0 0 56 56"><rect x="10" y="12" width="36" height="32" rx="6"/><path d="M18 24h20M18 32h12M22 6v6M34 6v6M22 44v6M34 44v6"/></svg>:<svg viewBox="0 0 56 56"><path d="M44 20a18 18 0 1 0 1 17M44 9v12H32M28 17v12l8 5"/></svg>}</span><strong>{label}</strong><span>{label==='Recovery'&&path==='normal'?'Standing by if needed':description}</span></div>)}</div><motion.div className="step-explanation" aria-live="polite" key={index} initial={{opacity:.7}} animate={{opacity:1}} transition={{duration:.22}}><h2>{step[1]}</h2><p>{step[2]}</p></motion.div><Controls index={index} count={steps.length} previous={()=>setIndex(i=>i-1)} next={()=>setIndex(i=>i+1)}/><p className="workspace-note">An illustration of the process. A retry can be claimed by any eligible worker.</p><Technical><p>A temporary assignment is called a <strong>lease</strong>. Check-ins are <strong>heartbeats</strong>. Each attempt gets a new <strong>fencing token</strong>, so an outdated worker cannot change the current task record.</p><p>This example separates expiry and recovery to explain their roles. The actual recording logs an expired attempt and its scheduled retry together. Recovery restarts the handler; external actions need their own duplicate protection.</p></Technical></div>;
}
const replayCopy = [
 ['Task saved','The task is safely recorded.','Relevo saved the request before the worker took it. The task is waiting for an eligible worker.'],
 ['Alex started','Alex begins the first attempt.','The first worker claimed the task. In this test, that worker was deliberately stopped after claiming it.'],
 ['Assignment expired','Ready for another try.','Alex’s assignment expired. Recovery recorded that attempt and made the saved task eligible for a retry after a short wait.'],
 ['Sam started','A new worker takes over.','Sam claimed the same saved task as a new attempt. The handler starts again from the beginning.'],
 ['Task completed','Finished after two attempts.','Sam’s result was accepted and saved. Alex’s expired attempt remains in the history.'],
];
function Replay() {
 const resource=useEvidence('worker-crash-recovery.json',validateCapture),[index,setIndex]=useState(0),[playing,setPlaying]=useState(false), calm=useReducedMotion();
 const data=resource.data;
 useEffect(()=>{if(calm)setPlaying(false);},[calm]);
 useEffect(()=>{const hide=()=>{if(document.hidden)setPlaying(false);};document.addEventListener('visibilitychange',hide);return()=>document.removeEventListener('visibilitychange',hide);},[]);
 useEffect(()=>{
  if(!playing || !data || calm)return;
  if(index>=data.events.length-1){setPlaying(false);return;}
  const timer=setTimeout(()=>setIndex(i=>i+1),1800);return()=>clearTimeout(timer);
 },[playing,index,data,calm]);
 const frame=data?replayFrame(data,index):null;
 const select=i=>{setPlaying(false);setIndex(i);};
 const text=replayCopy[index];
 return <div className="engine-workspace replay-workspace"><div className="workspace-toolbar"><span>Recorded worker recovery</span><span className="recording-label"><i/>Actual test recording</span></div><Loading resource={resource}>{data && <><Sequence labels={replayCopy.map(s=>s[0])} index={index} onSelect={select}/><div className="worker-lanes" aria-label="Two recorded attempts"><div><strong>Alex</strong><div className="lane-track"><motion.div initial={false} className="lane-fill first" animate={{width:index<1?'0%':index===1?'28%':'48%'}} transition={{duration:calm?0:.4}}/></div><span>{index<1?'Waiting':index===1?'Assigned':'Expired'}</span></div><div><strong>Sam</strong><div className="lane-track"><motion.div initial={false} className="lane-fill second" animate={{width:index<3?'0%':index===3?'66%':'100%'}} transition={{duration:calm?0:.4}}/></div><span>{index<3?'Waiting':index===3?'Assigned':'Completed'}</span></div></div><motion.div className="step-explanation" aria-live="polite" key={index} initial={{opacity:.7}} animate={{opacity:1}} transition={{duration:.22}}><h2>{text[1]}</h2><p>{text[2]}</p></motion.div><Controls index={index} count={data.events.length} previous={()=>select(index-1)} next={()=>select(index+1)} playing={playing} calm={calm} toggle={()=>{if(index===data.events.length-1)setIndex(0);setPlaying(v=>!v);}}/><p className="recorded-outcome"><span className="outcome-icon"><Glyph name="check"/></span>{index===4?'Completed after two attempts.':'This recording ends with a completed task.'}</p><Technical><p>Alex and Sam are friendly aliases for the two worker identities below. Steps are evenly spaced for readability. Playback is accelerated and is not a wall-clock reconstruction.</p><dl className="technical-facts"><div><dt>Job identifier</dt><dd>{data.job.id}</dd></div><div><dt>Recorded event</dt><dd>{frame.event.kind} · {frame.event.occurred_at}</dd></div><div><dt>Elapsed recorded time</dt><dd>{frame.elapsed.toFixed(3)} seconds</dd></div><div><dt>Current event state</dt><dd>{frame.state}</dd></div>{data.attempts.map((a,i)=><div key={a.id}><dt>{i?'Sam':'Alex'} · attempt {a.number}</dt><dd>{a.worker_id}<br/>Fencing token {a.fencing_token} · {a.state}</dd></div>)}</dl><h3>What the test deliberately changed</h3><p>The test killed the first worker after claiming, kept the scheduler stopped while the assignment expired, then restarted recovery. It also checked that an outdated completion was rejected. These are untimed test observations, not additional timestamped job events. No exact worker-death time is inferred.</p><p>Source: <code>{data.source.path}</code><br/>Revision: <code>{data.revision.git_commit}</code></p><Link className="text-action" href="/evidence/worker-crash-recovery.json">Read the original recording<Arrow/></Link></Technical></>}</Loading></div>;
}
export default function Engine() {
 const initial=()=>location.hash==='#replay'?'replay':'flow';
 const [tab,setTab]=useState(initial),refs=useRef([]);
 useEffect(()=>{const sync=()=>setTab(initial());window.addEventListener('hashchange',sync);window.addEventListener('popstate',sync);return()=>{window.removeEventListener('hashchange',sync);window.removeEventListener('popstate',sync);};},[]);
 function choose(next,focus=false){setTab(next);history.pushState({},'',`#${next}`);if(focus)refs.current[next==='flow'?0:1]?.focus();}
 function keys(e){if(['ArrowLeft','ArrowRight','Home','End'].includes(e.key)){e.preventDefault();choose(e.key==='Home'?'flow':e.key==='End'?'replay':tab==='flow'?'replay':'flow',true);}}
 return <main id="main" className="engine-page"><div className="engine-heading"><Intro title={<>Follow one <span>task.</span></>}>See the steps, then replay a recorded recovery test.</Intro><div className="segmented engine-tabs" role="tablist" aria-label="Engine view" onKeyDown={keys}>{['flow','replay'].map((key,i)=><button ref={el=>{refs.current[i]=el;}} key={key} id={`${key}-tab`} role="tab" aria-selected={tab===key} aria-controls={`${key}-panel`} tabIndex={tab===key?0:-1} onClick={()=>choose(key)}>{key==='flow'?'Flow':'Replay'}</button>)}</div></div><section role="tabpanel" id={`${tab}-panel`} aria-labelledby={`${tab}-tab`}>{tab==='flow'?<Flow/>:<Replay/>}</section></main>;
}
