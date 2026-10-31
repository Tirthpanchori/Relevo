import {useEffect,useRef} from 'react';

// Stationary cells regenerate independently. Nothing translates or follows a pointer.
const noise=(seed,epoch=0)=>{let n=(seed+Math.imul(epoch+1,374761393))|0;n=Math.imul(n^(n>>>13),1274126177);return ((n^(n>>>16))>>>0)/4294967296;};
export default function PixelField(){
 const ref=useRef(null);
 useEffect(()=>{
  const canvas=ref.current,ctx=canvas.getContext('2d');if(!ctx)return;
  const calm=matchMedia('(prefers-reduced-motion: reduce)');
  let frame=0,visible=false,last=0,time=0,width=0,height=0,points=[],epoch=-1;
  function targets(cycle){for(const p of points){p.from=p.to??0;p.to=noise(p.seed,cycle)<p.density?.35+noise(p.seed,cycle+11)*.55:0;}epoch=cycle;}
  function paint(){
   const cycle=Math.floor(time/.6);if(cycle!==epoch)targets(cycle);
   const t=Math.min(1,(time/.6-cycle)/.72),mix=t*t*(3-2*t);
   ctx.clearRect(0,0,width,height);ctx.fillStyle='#deef59';
   for(const p of points){const alpha=calm.matches?p.to:p.from+(p.to-p.from)*mix;if(alpha<.055)continue;ctx.globalAlpha=alpha;ctx.fillRect(p.x,p.y,2,2);}
   ctx.globalAlpha=1;canvas.dataset.frames=String(Number(canvas.dataset.frames||0)+1);canvas.dataset.epoch=String(cycle);
  }
  function resize(){
   width=canvas.clientWidth;height=canvas.clientHeight;const dpr=Math.min(devicePixelRatio,1.5);
   canvas.width=Math.round(width*dpr);canvas.height=Math.round(height*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);
   points=[];epoch=-1;
   for(let y=0;y<height;y+=5)for(let x=0;x<width;x+=5){
    const seed=x*137+y*277+7141,patch=noise(Math.floor(x/65)*811+Math.floor(y/65)*271);
    const density=(.006+.75*Math.pow(x/Math.max(1,width),3.5))*(.55+patch);
    points.push({x,y,seed,density,from:0,to:undefined});
   }
   targets(Math.floor(time/.6));for(const p of points)p.from=p.to;paint();
  }
  function tick(now){frame=0;if(!visible||document.hidden||calm.matches){stop();if(calm.matches)paint();return;}if(now-last>=1000/24){time+=last?Math.min((now-last)/1000,.1):0;last=now;paint();}frame=requestAnimationFrame(tick);}
  function stop(){cancelAnimationFrame(frame);frame=0;last=0;canvas.dataset.running='false';}
  function sync(){stop();if(visible&&!document.hidden&&!calm.matches){canvas.dataset.running='true';frame=requestAnimationFrame(tick);}else if(calm.matches){paint();}}
  const observer=new IntersectionObserver(entries=>{visible=entries[entries.length-1].isIntersecting;sync();});observer.observe(canvas);
  const size=new ResizeObserver(resize);size.observe(canvas);resize();
  document.addEventListener('visibilitychange',sync);calm.addEventListener('change',sync);
  return()=>{stop();observer.disconnect();size.disconnect();document.removeEventListener('visibilitychange',sync);calm.removeEventListener('change',sync);};
 },[]);
 return <div className="hero-pixels" data-pixel-field="hero" aria-hidden="true"><canvas ref={ref}/></div>;
}
