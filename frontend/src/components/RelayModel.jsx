import { useEffect, useRef, useState } from 'react';
import ScrollReveal from './ScrollReveal.jsx';
import { useScroll, useMotionValueEvent, useReducedMotion, useSpring } from 'motion/react';
import { slabOf, cylinder, iso, depthOf, boxCorners, fitProjection } from '../anatomy/iso-kit.mjs';
export const levels=[
 {id:'coordinator',name:'Coordinator',title:'A front desk for the work.',copy:'Receives requests and checks who may update a task. Acceptance is confirmed after the task is saved.'},
 {id:'workers',name:'Workers',title:'The part that does the work.',copy:'Workers run task handlers and check in while working. Their permission to report a result is temporary.'},
 {id:'scheduler',name:'Recovery',title:'Another try, when it is allowed.',copy:'Recovery finds expired assignments and schedules another eligible attempt within the task’s retry limit.'},
 {id:'database',name:'Saved record',title:'A record that stays.',copy:'PostgreSQL keeps the task, its attempts, and the outcome together. A new attempt adds to that history.'},
];
const plan=(x,y,w,d,r=2)=>({x,y,w,d,r});
const P=fitProjection(boxCorners(plan(0,0,680,220),0,440),1120,640,{pad:20,azimuth:77,elevation:23});
const palettes={steel:['#dfe1cf','#b4bbaa','#869487','#667d71','#eff0df'],dark:['#456357','#334e45','#233f36','#19372e','#627e6c'],lime:['#d9e85c','#b0c247','#82963b','#63752d','#eef58e']};
const parts=[];
function block(group,x,y,z,w,d,h,material='steel',r=2,signal=false){parts.push({group,paths:slabOf(plan(x,y,w,d,r),z,h,P,5,.6),material,signal,depth:depthOf([x+w/2,y+d/2,z+h/2],P)});}
function post(group,x,y,z,r,h,material='steel'){parts.push({group,paths:cylinder(x,y,r,z,h,P,20,.5),material,depth:depthOf([x,y,z+h/2],P)});}
// Storage foundation, record drawers and the persistent task cartridge.
for(const x of [42,625])for(const y of [24,184]){post('database',x,y,0,14,8,'dark');post('database',x,y,8,10,7);}
block('database',16,0,15,640,208,14,'dark',7);block('database',24,8,29,624,192,7,'steel',4);
for(const x of [105,250,395]){block('database',x,180,20,110,18,12,'dark');block('database',x+35,198,23,40,3,5,'steel',1);}
block('database',286,60,36,98,108,18,'dark',4);block('database',294,68,54,82,91,62,'lime',6,true);
for(let i=0;i<7;i++)block('database',302+i*9,76,116,3,72,1.2,'dark',.5);
for(const x of [42,632])for(const y of [16,192]){post('database',x,y,36,4.8,3);post('database',x,y,39,1.5,1,'dark');}
// Recovery drive on its own tray below the worker rail.
// U-frame leaves a real aperture around the storage-mounted task cartridge.
block('scheduler',46,14,36,224,174,8,'dark',4);block('scheduler',400,14,36,221,174,8,'dark',4);block('scheduler',270,14,36,130,30,8,'dark');block('scheduler',270,172,36,130,16,8,'dark');block('scheduler',52,20,44,90,138,9,'steel',3,true);
for(const x of [80,113]){post('scheduler',x,83,53,16,8,'dark');post('scheduler',x,83,61,10,4);post('scheduler',x,83,65,4,3,'dark');}
block('scheduler',621,49,36,20,118,17,'dark');block('scheduler',625,54,53,14,108,80,'dark',3);block('scheduler',616,71,85,12,76,17,'steel');block('scheduler',611,99,96,20,24,21,'lime',3,true);
// Removable worker rail and carriages.
for(const y of [24,168]){block('workers',46,y,44,560,14,8,'dark');block('workers',64,y+3,52,524,8,9);for(const x of [57,595]){block('workers',x-12,y-5,44,24,24,15,'dark');post('workers',x,y+7,59,4,3);}}
for(const x of [138,450]){block('workers',x,24,61,88,158,12,'dark',4);block('workers',x+6,43,73,76,117,48,'steel',6);block('workers',x+12,49,121,64,104,8,'steel',4,true);for(let i=0;i<7;i++)block('workers',x+16+i*8,62,129,3,72,1.1,'dark',.5);for(const y of [52,146])for(const dx of [14,72])post('workers',x+dx,y,129,2.5,1);block('workers',x+28,162,85,32,4,18,'dark',3);for(const dx of [34,48])post('workers',x+dx,169,88,2,2);}
// Intake/control deck with real controls rather than an unexplained lid.
for(const x of [70,604])for(const y of [15,193]){block('database',x-13,y-10,36,26,20,9,'dark');post('database',x,y,45,5,105);post('database',x,y,45,8,14);}
block('coordinator',51,0,150,572,208,10,'steel',6);block('coordinator',61,10,160,552,188,3,'steel',4);block('coordinator',242,50,163,190,103,14,'dark',5);block('coordinator',254,61,177,166,78,4,'steel',3,true);block('coordinator',266,82,181,112,12,1.5,'dark');for(const x of [390,405])post('coordinator',x,115,181,4,2,'lime');
for(const x of [100,495])for(let i=0;i<8;i++)block('coordinator',x+i*5,72,163,2,53,1,'dark',.5);
for(const x of [70,604])for(const y of [15,193]){post('coordinator',x,y,163,5.5,2,'dark');post('coordinator',x,y,165,2.5,1);}
const assemblies=Object.fromEntries(['database','scheduler','workers','coordinator'].map(id=>[id,parts.filter(p=>p.group===id).sort((a,b)=>a.depth-b.depth)]));
function Solid({part}){const p=part.paths,c=palettes[part.material];return <g className={`solid ${part.material}`}><path d={p.fill} fill={c[0]}/>{p.shades.map((d,i)=><path key={i} d={d} fill={c[i]}/>)}<path className={part.signal?'signal-face':undefined} d={p.top} fill={c[4]}/><path d={p.crease} className="solid-crease"/><path d={p.outline} className="solid-edge"/>{p.bevel&&<path d={p.bevel} className="solid-bevel"/>}</g>;}
const stops=[[0,0,0],[100,0,0],[195,90,0],[255,145,75],[265,155,90]];
const smooth=t=>{const v=Math.max(0,Math.min(1,t));return v*v*(3-2*v);};
function shift(z,x=0){const a=iso([0,0,0],P),b=iso([x,0,z],P);return {x:b[0]-a[0],y:b[1]-a[1]};}
export default function RelayModel(){
 const section=useRef(null),nodes=useRef({}),camera=useRef(null),bounds=useRef({}),guides=useRef([]),current=useRef(0),[stage,setStage]=useState(0),reduced=useReducedMotion();
 const [shortViewport,setShortViewport]=useState(()=>matchMedia('(max-height: 650px)').matches),calm=reduced||shortViewport;
 useEffect(()=>{const query=matchMedia('(max-height: 650px)'),update=()=>setShortViewport(query.matches);query.addEventListener('change',update);return()=>query.removeEventListener('change',update);},[]);
 const {scrollYProgress}=useScroll({target:section,offset:['start start','end end']});
 const reveal=useSpring(scrollYProgress,{stiffness:110,damping:26,mass:.5});
 function draw(progress){const t=Math.max(0,Math.min(1,progress)),index=Math.min(3,Math.floor(t*4)),mix=smooth((t*4-index)*1.45),pose=calm?stops[4]:stops[index].map((v,i)=>v+(stops[index+1][i]-v)*mix);const moved={database:{x:0,y:0}};for(const [i,id] of ['coordinator','workers','scheduler'].entries()){const delta=shift(pose[i],id==='workers'?-18*pose[1]/155:0);moved[id]=delta;nodes.current[id]?.setAttribute('transform',`translate(${delta.x} ${delta.y})`);}const boxes=Object.entries(bounds.current).map(([id,b])=>({x:b.x+moved[id].x,y:b.y+moved[id].y,w:b.width,h:b.height}));if(boxes.length===4){const x=Math.min(...boxes.map(b=>b.x)),y=Math.min(...boxes.map(b=>b.y)),w=Math.max(...boxes.map(b=>b.x+b.w))-x,h=Math.max(...boxes.map(b=>b.y+b.h))-y,scale=Math.min(1.6,860/w,550/h);camera.current?.setAttribute('transform',`translate(480 320) scale(${scale}) translate(${-x-w/2} ${-y-h/2})`);}for(const [i,x] of [70,604].entries()){const a=iso([x,15,150],P),b=iso([x,15,150+pose[0]],P);guides.current[i]?.setAttribute('d',`M${a[0]} ${a[1]}L${b[0]} ${b[1]}`);}section.current?.setAttribute('data-model-progress',t.toFixed(3));if(current.current!==index){current.current=index;setStage(index);}}
 useMotionValueEvent(reveal,'change',draw);useEffect(()=>{bounds.current=Object.fromEntries(Object.entries(nodes.current).filter(([,node])=>node).map(([id,node])=>[id,node.getBBox()]));draw(scrollYProgress.get());},[calm]);
 return <section ref={section} id="model" className={`model-section four-level-model ${calm?'still':''}`} data-active-level={levels[stage].id}><div className="model-sticky"><ScrollReveal name="model-heading" className="model-heading"><h2>Saved. Tried. Ready to try again.</h2><p>Four responsibilities. One task that stays accounted for.</p></ScrollReveal><ol className="level-indicator" aria-label="System levels">{levels.map((level,i)=><li key={level.id} aria-current={!calm&&stage===i?'step':undefined}><span>{i+1}</span>{level.name}</li>)}</ol><figure className="relay-figure"><svg viewBox="0 0 960 640" data-anatomy-model="four-level-rack" role="img" aria-labelledby="model-title model-desc"><title id="model-title">Four levels of Relevo: coordinator, workers, recovery and saved record</title><desc id="model-desc">Scrolling exposes each responsible assembly, from intake controls through worker rails and recovery to storage. The lime task cartridge stays connected to the foundation. This physical model illustrates software.</desc><defs><filter id="rack-shadow" x="-20%" y="-100%" width="140%" height="300%"><feGaussianBlur stdDeviation="14"/></filter></defs><g ref={camera} className="model-camera"><ellipse cx="550" cy="565" rx="390" ry="22" fill="#203e31" opacity=".15" filter="url(#rack-shadow)"/>{[0,1].map(i=><path key={i} ref={node=>{guides.current[i]=node;}} className="assembly-guide"/>)}{Object.entries(assemblies).map(([id,items])=><g key={id} ref={node=>{nodes.current[id]=node;}} className="model-assembly" data-assembly={id} data-current={calm||levels[stage].id===id?'true':'false'}>{items.map((part,i)=><Solid key={i} part={part}/>)}</g>)}</g></svg><figcaption className="model-caption">{calm?<div className="static-levels">{levels.map(level=><section key={level.id}><h3>{level.name}</h3><p>{level.copy}</p></section>)}</div>:<div key={levels[stage].id} className="level-explanation"><h3>{levels[stage].title}</h3><p>{levels[stage].copy}</p></div>}</figcaption></figure>{!calm&&<p className="scroll-hint">{stage===3?'The task stays. Scroll to continue.':'Scroll to reveal the next responsibility'}<span className="scroll-line" aria-hidden="true"/></p>}</div></section>;
}
