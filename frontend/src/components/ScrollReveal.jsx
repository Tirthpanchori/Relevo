import {useLayoutEffect,useRef,useState} from 'react';
import {motion,useReducedMotion} from 'motion/react';

// A visible default; only offscreen groups are armed for their first entrance.
export default function ScrollReveal({children,className='',name,delay=0,enabled=true,...props}){
 const ref=useRef(null),calm=useReducedMotion();
 const [shown,setShown]=useState(true),[focused,setFocused]=useState(false);
 useLayoutEffect(()=>{
  const node=ref.current;if(!enabled||calm){setShown(true);return;}
  if(node.getBoundingClientRect().top<innerHeight-65)return;
  setShown(false);
  const observer=new IntersectionObserver(entries=>{if(entries.some(e=>e.isIntersecting)){setShown(true);observer.disconnect();}},{rootMargin:'0px 0px -65px 0px',threshold:0});
  observer.observe(node);return()=>observer.disconnect();
 },[enabled,calm]);
 return <motion.div {...props} ref={ref} className={className} data-reveal={name} data-reveal-state={shown?'shown':'pending'} initial={false} animate={{opacity:shown?1:0,y:shown?0:24}} transition={{duration:calm||focused?0:.65,delay:shown&&!focused?delay:0,ease:[.16,1,.3,1]}} onFocusCapture={()=>{setFocused(true);setShown(true);}}>{children}</motion.div>;
}
