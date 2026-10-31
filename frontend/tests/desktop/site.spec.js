import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import { readFile, mkdir, writeFile } from 'node:fs/promises';
import { resolve } from 'node:path';

const shots=resolve('../.impeccable/review/release-desktop');
const recording=JSON.parse(await readFile('public/evidence/worker-crash-recovery.json','utf8'));
const measurements=JSON.parse(await readFile('public/evidence/benchmark-summary.json','utf8'));
test.beforeAll(async()=>mkdir(shots,{recursive:true}));
async function fullCapture(page,file){
 if(await page.locator('.home-hero').count()){for(const selector of ['#model','.example-section','.recovery-story','.faq-section','.docs-ending','footer']){await page.locator(selector).scrollIntoViewIfNeeded();await page.waitForTimeout(800);}}
 await page.mouse.move(10,10);
 await page.evaluate(()=>{window.scrollTo({top:0,behavior:'instant'});if(document.activeElement instanceof HTMLElement)document.activeElement.blur();});
 await page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
 await page.screenshot({path:resolve(shots,file),fullPage:true});
}

test('six desktop pages, direct entries, assets and utility destinations',async({page,request})=>{
 const failures=[],requests=[];
 page.on('pageerror',e=>failures.push(e.message));
 page.on('response',r=>{if(r.status()>=400)failures.push(`${r.status()} ${r.url()}`);});
 page.on('request',r=>requests.push(r));
 const routes=['','engine/','results/','docs/','about/','privacy/'];
 for(const width of [1440,1920]){
  await page.setViewportSize({width,height:1000});
  for(const route of routes){
   await page.goto(route || './');await page.evaluate(()=>document.fonts.ready);
   await expect(page.locator('main h1')).toBeVisible();
   await expect(page.locator('header nav a')).toHaveText(['Home','Engine','Results','Docs']);
   expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
   if(width===1440){await fullCapture(page,`${route.replace('/','')||'home'}-desktop.png`);}
  }
 }
 expect(failures).toEqual([]);
 expect(requests.every(r=>r.method()==='GET'&&new URL(r.url()).origin==='http://127.0.0.1:4173')).toBe(true);
 for(const file of ['llms.txt','sitemap.xml','evidence/worker-crash-recovery.json','evidence/benchmark-summary.json'])expect((await request.get(file)).ok()).toBe(true);
 const sitemap=await(await request.get('sitemap.xml')).text();expect((sitemap.match(/<loc>/g)||[]).length).toBe(6);
 await page.goto('404.html');await expect(page.getByRole('heading',{name:'This path ends here.'})).toBeVisible();
 await page.getByRole('link',{name:'Back to Home',exact:true}).click();await expect(page).toHaveURL(/4173\/$/);
});

test('four explanatory depths, reverse/fast scrolling, type and highlighted recover',async({page})=>{
 await page.goto('./');await page.evaluate(()=>document.fonts.ready);
 await expect(page.locator('[data-anatomy-model]')).toHaveCount(1);await expect(page.locator('.home-hero [data-anatomy-model]')).toHaveCount(0);
 expect(await page.locator('h1').evaluate(e=>getComputedStyle(e).fontSize)).toBe('76px');
 expect(await page.locator('.recover-word').evaluate(e=>getComputedStyle(e).color)).toBe('rgb(222, 239, 89)');
 await expect(page.locator('main a[href="/engine/"]')).toHaveCount(1);
 const model=page.locator('#model'),position=await model.evaluate(el=>({start:el.offsetTop,length:el.offsetHeight-innerHeight}));
 const ids=['coordinator','workers','scheduler','database'];
 for(const [i,t] of [.02,.32,.59,.88].entries()){
  await page.evaluate(y=>scrollTo({top:y,behavior:'instant'}),position.start+t*position.length);
  await expect(model).toHaveAttribute('data-active-level',ids[i]);await expect(page.locator('.level-indicator [aria-current]')).toHaveCount(1);
  await expect(page.locator('[data-assembly="'+ids[i]+'"]').first()).toHaveAttribute('data-current','true');
  await expect(page.locator('.model-caption h3')).toBeVisible();const contained=await page.locator('[data-anatomy-model]').evaluate(svg=>{const r=svg.getBoundingClientRect();return [...svg.querySelectorAll('.model-assembly')].every(g=>{const b=g.getBoundingClientRect();return b.left>=r.left-8&&b.right<=r.right+8&&b.top>=r.top-8&&b.bottom<=r.bottom+8;});});expect(contained).toBe(true);expect(await page.locator('[data-assembly="database"]').getAttribute('transform')).toBeNull();
  await expect.poll(async()=>Math.abs(Number(await model.getAttribute('data-model-progress'))-t)).toBeLessThan(.008);await page.waitForTimeout(180);
  await page.mouse.move(5,5);await page.screenshot({path:resolve(shots,'model-level-'+(i+1)+'-desktop.png')});
 }
 for(const [t,id] of [[.32,'workers'],[1,'database'],[.02,'coordinator']]){await page.evaluate(y=>scrollTo({top:y,behavior:'instant'}),position.start+t*position.length);await expect(model).toHaveAttribute('data-active-level',id);}
});

test('hero-only pixel pattern regenerates edge-to-edge and suspends offscreen/hidden',async({page})=>{
 await page.goto('./');await expect(page.locator('.pixel-band')).toHaveCount(0);const canvas=page.locator('.hero-pixels canvas');await expect(canvas).toHaveAttribute('data-running','true');
 const before=Number(await canvas.getAttribute('data-frames'));await expect.poll(async()=>Number(await canvas.getAttribute('data-frames'))).toBeGreaterThan(before+2);
 const data=await canvas.evaluate(c=>{const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let left=0,right=0;for(let y=0;y<c.height;y++)for(let x=0;x<Math.floor(c.width*.1);x++){left+=d[(y*c.width+x)*4+3]>0;right+=d[(y*c.width+c.width-x-1)*4+3]>0;}return {width:c.clientWidth,viewport:innerWidth,left,right};});
 expect(data.width).toBe(data.viewport);expect(data.left).toBeGreaterThan(20);expect(data.right).toBeGreaterThan(20);
 await page.locator('.faq-section').scrollIntoViewIfNeeded();await expect(canvas).toHaveAttribute('data-running','false');let count=await canvas.getAttribute('data-frames');await page.waitForTimeout(180);expect(await canvas.getAttribute('data-frames')).toBe(count);
 await page.evaluate(()=>scrollTo({top:0,behavior:'instant'}));await expect(canvas).toHaveAttribute('data-running','true');await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});await expect(canvas).toHaveAttribute('data-running','false');
});

test('visible fill sweep, press/focus feedback and persistent selected states',async({page})=>{
 await page.goto('./');const button=page.locator('.home-hero .action');const before=await button.evaluate(e=>getComputedStyle(e,'::before').transform);await button.hover();await expect.poll(()=>button.evaluate(e=>getComputedStyle(e,'::before').transform)).not.toBe(before);await button.focus();await expect(button).toBeFocused();
 await page.goto('engine/#flow');const selected=page.getByRole('button',{name:'Work completes',exact:true}),other=page.getByRole('button',{name:'Worker stops',exact:true});await other.hover();expect(await selected.evaluate(e=>getComputedStyle(e).backgroundColor)).not.toBe(await other.evaluate(e=>getComputedStyle(e).backgroundColor));
});

test('Flow normal/interrupted paths and Recovery highlight; accessible tabs/history',async({page})=>{
 await page.goto('engine/#flow');
 await expect(page.locator('.sequence li')).toHaveCount(6);
 await expect(page.locator('[data-component=application]')).toHaveClass(/active/);
 await page.getByRole('button',{name:'Task completed',exact:true}).click();await expect(page.getByRole('heading',{name:'The result is saved.'})).toBeVisible();
 await page.getByRole('button',{name:'Worker stops',exact:true}).click();await expect(page.locator('.sequence li')).toHaveCount(8);
 await page.getByRole('button',{name:'Recovery',exact:true}).click();await expect(page.locator('[data-component="recovery"]')).toHaveClass(/active/);
 await expect(page.getByRole('heading',{name:'Make room for another try.'})).toBeVisible();
 await fullCapture(page,'flow-recovery-desktop.png');
 const flow=page.getByRole('tab',{name:'Flow',exact:true}), replay=page.getByRole('tab',{name:'Replay',exact:true});
 await flow.focus();await page.keyboard.press('ArrowRight');await expect(replay).toBeFocused();await expect(replay).toHaveAttribute('aria-selected','true');
 await flow.click();await page.goBack();await expect(replay).toHaveAttribute('aria-selected','true');
 await replay.focus();await page.keyboard.press('Home');await expect(flow).toBeFocused();
});

test('Replay shows actual steps with aliases, optional exact facts and untimed interventions',async({page})=>{
 await page.goto('engine/#replay');await expect(page.getByRole('heading',{name:'The task is safely recorded.'})).toBeVisible();
 await expect(page.getByText(recording.job.id,{exact:true})).not.toBeVisible();
 await page.getByRole('button',{name:'Next step'}).click();await expect(page.getByRole('heading',{name:'Alex begins the first attempt.'})).toBeVisible();
 await page.getByRole('button',{name:'Next step'}).click();await expect(page.getByRole('heading',{name:'Ready for another try.'})).toBeVisible();
 await fullCapture(page,'replay-recovery-desktop.png');
 await page.locator('summary').click();await expect(page.locator('.technical-content')).toContainText(recording.job.id);await expect(page.locator('.technical-content')).toContainText(recording.events[2].occurred_at);await expect(page.locator('.technical-content')).toContainText('untimed test observations');
 for(const attempt of recording.attempts)await expect(page.locator('.technical-content')).toContainText(attempt.worker_id);
 await page.getByRole('button',{name:'Task completed',exact:true}).click();await expect(page.getByRole('heading',{name:'Finished after two attempts.'})).toBeVisible();await expect(page.getByRole('button',{name:'Next step'})).toBeDisabled();
 await page.getByRole('button',{name:'Play',exact:true}).click();await expect(page.getByRole('button',{name:'Pause',exact:true})).toBeVisible();
 await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});await expect(page.getByRole('button',{name:'Play',exact:true})).toBeVisible();
});

test('Results comparisons reproduce retained measurements and preserve all filters',async({page})=>{
 await page.goto('results/');await expect(page.locator('.results-table tbody tr')).toHaveCount(3);
 let row=measurements.repeated.rows.find(r=>r.workload==='short_hash'&&r.workers===1);
 await expect(page.locator('tbody tr').first()).toContainText(row.baseline.throughput.toFixed(3));
 await page.getByRole('button',{name:'Confirmation',exact:true}).click();await page.getByRole('button',{name:'Timed tasks',exact:true}).click();
 await page.getByRole('combobox',{name:'Measurement'}).selectOption('queueP95');
 row=measurements.confirmation.rows.find(r=>r.workload==='long_timed'&&r.workers===1);
 await expect(page.locator('tbody tr').first()).toContainText(row.candidate.queueP95.toFixed(1));
 await expect(page.getByRole('button',{name:'Timed tasks',exact:true})).toHaveAttribute('aria-pressed','true');
 await fullCapture(page,'results-filtered-desktop.png');
});

test('FAQ reverses immediately, closes accessibly and opens one answer at a time',async({page})=>{
 await page.goto('./');
 const first=page.getByRole('button',{name:'What does Relevo actually do?'}),second=page.getByRole('button',{name:'What is a worker?',exact:true});
 await first.scrollIntoViewIfNeeded();await first.click();await expect(first).toHaveAttribute('aria-expanded','true');await first.click();await expect(first).toHaveAttribute('aria-expanded','false');
 await expect.poll(()=>page.locator('#answer-0').evaluate(el=>el.getBoundingClientRect().height)).toBe(0);
 await first.click();await second.click();await expect(first).toHaveAttribute('aria-expanded','false');await expect(second).toHaveAttribute('aria-expanded','true');
 await expect(page.locator('#answer-0')).toHaveAttribute('inert','');
 await page.locator('.faq-section').evaluate(el=>window.scrollTo({top:el.offsetTop-60,behavior:'instant'}));
 await expect.poll(()=>page.locator('#answer-1').evaluate(el=>el.getBoundingClientRect().height)).toBeGreaterThan(60);
 await page.screenshot({path:resolve(shots,'faq-open-desktop.png')});
 await page.goto('docs/');const button=page.getByRole('button',{name:'Copy terminal commands'}).first();await button.focus();await page.keyboard.press('Enter');await expect(button).toHaveText(/Copied|Select to copy/);
});

test('reduced motion has a readable static model, immediate FAQ and manual Replay',async({page})=>{
 await page.emulateMedia({reducedMotion:'reduce'});await page.goto('./');
 await expect(page.locator('#model')).toHaveClass(/still/);await expect(page.locator('.static-levels section')).toHaveCount(4);await expect(page.locator('.hero-pixels canvas')).toHaveAttribute('data-running','false');
 const q=page.getByRole('button',{name:'Can a task still fail?'});await q.click();await q.click();expect(await page.locator('#answer-3').evaluate(el=>el.getBoundingClientRect().height)).toBe(0);
 await page.goto('engine/#replay');await expect(page.getByRole('button',{name:'Play',exact:true})).toBeDisabled();await page.getByRole('button',{name:'Next step'}).click();await expect(page.getByRole('heading',{name:'Alex begins the first attempt.'})).toBeVisible();
});

test('recording/measurement fetch errors and invalid provenance can recover',async({page})=>{
 await page.route('**/evidence/worker-crash-recovery.json',route=>route.fulfill({status:200,contentType:'application/json',body:'{"events":[]}'}));await page.goto('engine/#replay');await expect(page.getByRole('alert')).toContainText('couldn’t load');await page.unroute('**/evidence/worker-crash-recovery.json');await page.getByRole('button',{name:'Try again',exact:true}).click();await expect(page.getByRole('heading',{name:'The task is safely recorded.'})).toBeVisible();
 await page.route('**/evidence/benchmark-summary.json',route=>route.fulfill({status:503,body:'Unavailable'}));await page.goto('results/');await expect(page.getByRole('alert')).toBeVisible();await page.unroute('**/evidence/benchmark-summary.json');await page.getByRole('button',{name:'Try again',exact:true}).click();await expect(page.locator('tbody tr')).toHaveCount(3);
});

test('desktop accessibility scan of all six pages and both Engine views',async({page})=>{
 const report=[];
 for(const path of ['/','/engine/#flow','/engine/#replay','/results/','/docs/','/about/','/privacy/']){
  await page.goto(path.slice(1)||'./');await expect(page.locator('main h1')).toBeVisible();await page.evaluate(()=>document.fonts.ready);
  if(path.includes('replay'))await expect(page.getByRole('heading',{name:'The task is safely recorded.'})).toBeVisible();
  if(path==='/results/')await expect(page.locator('tbody tr')).toHaveCount(3);
  if(path==='/'){await fullCapture(page,'home-desktop.png');await expect(page.locator('[data-reveal-state="pending"]')).toHaveCount(0);await page.waitForTimeout(800);}
  const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();report.push({path,violations:result.violations});
 }
 await writeFile('../artifacts/verification/release-desktop-accessibility.json',JSON.stringify(report,null,2));
 expect(report.flatMap(row=>row.violations.map(v=>({path:row.path,id:v.id,nodes:v.nodes.map(n=>n.target)})))).toEqual([]);
});


test('Docs follows reading position in both directions and direct fragment loads',async({page})=>{
 await page.goto('docs/');
 await expect(page.locator('.docs-grid')).toBeVisible();await page.evaluate(()=>document.fonts.ready.then(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))));
 const nav=page.getByRole('navigation',{name:'Documentation sections'});
 for(const id of ['quickstart','concepts','api','configuration','evidence','concepts','quickstart']){
  await page.locator('#'+id).evaluate(el=>window.scrollTo({top:el.offsetTop-100,behavior:'instant'}));
  await expect(nav.locator('a[aria-current=location]')).toHaveAttribute('href','#'+id);
 }
 await page.screenshot({path:resolve(shots,'docs-scrollspy-desktop.png')});
 await page.goto('about/');await page.goto('docs/#configuration');await expect(nav.locator('a[aria-current=location]')).toHaveAttribute('href','#configuration');await page.reload();await expect(nav.locator('a[aria-current=location]')).toHaveAttribute('href','#configuration');
 await nav.getByRole('link',{name:'Use the API',exact:true}).click();await expect(nav.locator('a[aria-current=location]')).toHaveAttribute('href','#api');
 await expect.poll(()=>page.locator('#api').evaluate(el=>Math.abs(el.getBoundingClientRect().top-124))).toBeLessThan(8);await page.waitForTimeout(350);await page.mouse.move(2,2);await page.screenshot({path:resolve(shots,'docs-active-api-desktop.png')});
});

test('consistent brand, spacious hero, regenerating pixel grid and reversible report hover',async({page})=>{
 await page.goto('./');await expect(page).toHaveTitle('Relevo — Background work can recover');
 await page.evaluate(()=>document.fonts.ready);await expect(page.locator('.footer-word .wordmark')).toBeVisible();
 const hero=await page.locator('.home-hero').boundingBox();expect(hero.height).toBeGreaterThan(600);
 const brand=page.locator('.header .brand .wordmark-name'),mask=await brand.evaluate(el=>getComputedStyle(el,'::after').clipPath);
 await brand.hover();await expect.poll(()=>brand.evaluate(el=>getComputedStyle(el,'::after').clipPath)).not.toBe(mask);
 await page.screenshot({path:resolve(shots,'hero-brand-hover-desktop.png')});
 const canvas=page.locator('.hero-pixels canvas');const fingerprint=()=>canvas.evaluate(c=>{const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let hash=2166136261;for(let i=3;i<d.length;i+=4)hash=Math.imul(hash^(d[i]>0?1:0),16777619);return hash>>>0;});
 const grid=await fingerprint();await expect.poll(fingerprint).not.toBe(grid);
 const stationary=await canvas.evaluate(c=>{const dpr=c.width/c.clientWidth,a=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let offgrid=0;for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++)if(a[(y*c.width+x)*4+3]>0){const gx=(x+.5)/dpr%5,gy=(y+.5)/dpr%5;if(gx>2.4&&gx<4.6||gy>2.4&&gy<4.6)offgrid++;}return offgrid;});expect(stationary).toBe(0);
 const paper=page.locator('.report-sheet'),ticket=page.locator('.worker-ticket');
 await page.locator('.example-section').scrollIntoViewIfNeeded();await page.mouse.move(2,2);await page.waitForTimeout(600);
 const rest=await paper.evaluate(el=>getComputedStyle(el).transform),ticketRest=await ticket.evaluate(el=>getComputedStyle(el).transform);
 await paper.hover();await expect.poll(()=>paper.evaluate(el=>getComputedStyle(el).transform)).not.toBe(rest);
 await page.waitForTimeout(600);await expect.poll(()=>ticket.evaluate(el=>getComputedStyle(el).transform)).not.toBe(ticketRest);
 await page.screenshot({path:resolve(shots,'report-hover-desktop.png')});await page.mouse.move(2,2);
 await expect.poll(()=>paper.evaluate(el=>getComputedStyle(el).transform)).toBe(rest);await expect.poll(()=>ticket.evaluate(el=>getComputedStyle(el).transform)).toBe(ticketRest);
 await page.screenshot({path:resolve(shots,'report-rest-desktop.png')});
 await page.goto('engine/');await expect(page).toHaveTitle('Relevo — Engine');
});

test('hero contains only copy and active pixels, with no report animation',async({page})=>{
 await page.goto('./');await expect(page.locator('h1')).toBeVisible();await expect(page.locator('.home-hero figure,.hero-example,.hero-stage')).toHaveCount(0);await expect(page.locator('.home-hero button')).toHaveCount(0);await expect(page.locator('.hero-pixels canvas')).toHaveAttribute('data-running','true');await expect(page.locator('.home-hero .action')).toHaveCount(1);
 await page.screenshot({path:resolve(shots,'hero-1440.png')});await page.setViewportSize({width:1920,height:1000});await page.screenshot({path:resolve(shots,'hero-1920.png')});
 await page.emulateMedia({reducedMotion:'reduce'});const canvas=page.locator('.hero-pixels canvas');await expect(canvas).toHaveAttribute('data-running','false');const frames=await canvas.getAttribute('data-frames');await page.waitForTimeout(250);expect(await canvas.getAttribute('data-frames')).toBe(frames);await expect(page.locator('.home-hero h1')).toBeVisible();
});

test('Home sections enter on scroll, persist on return and reveal immediately for keyboard/reduced motion',async({page})=>{
 await page.goto('./');
 for(const name of ['example-copy','recovery-copy','faq-heading','docs-action','footer'])await expect(page.locator('[data-reveal="'+name+'"]').first()).toHaveAttribute('data-reveal-state','pending');
 const recovery=page.locator('[data-reveal="recovery-copy"]');await page.locator('.recovery-story').scrollIntoViewIfNeeded();await expect(recovery).toHaveAttribute('data-reveal-state','shown');await expect.poll(()=>recovery.evaluate(e=>getComputedStyle(e).opacity)).toBe('1');
 await page.screenshot({path:resolve(shots,'recovery-revealed-desktop.png')});await page.evaluate(()=>scrollTo({top:0,behavior:'instant'}));await expect(recovery).toHaveAttribute('data-reveal-state','shown');
 const docs=page.locator('[data-reveal="docs-action"]');await expect(docs).toHaveAttribute('data-reveal-state','pending');await docs.getByRole('link').focus();await expect(docs).toHaveAttribute('data-reveal-state','shown');await expect.poll(()=>docs.evaluate(e=>getComputedStyle(e).opacity)).toBe('1');await expect(docs.getByRole('link')).toBeFocused();
 await page.emulateMedia({reducedMotion:'reduce'});await page.reload();await expect(page.locator('[data-reveal-state="pending"]')).toHaveCount(0);
});

test('navigation stays visible, becomes translucent on scroll and restores at the top',async({page})=>{
 for(const route of ['./','engine/','results/','docs/','about/','privacy/']){
  await page.goto(route);await expect(page.locator('main h1')).toBeVisible();const header=page.locator('header');await expect(header).toHaveAttribute('data-scrolled','false');
  await page.evaluate(()=>scrollTo({top:600,behavior:'instant'}));await expect(header).toHaveAttribute('data-scrolled','true');await expect.poll(()=>header.evaluate(e=>Math.round(e.getBoundingClientRect().top))).toBe(0);
  await expect.poll(()=>header.evaluate(e=>getComputedStyle(e).backgroundColor)).toBe('rgba(16, 51, 46, 0.9)');expect(await header.evaluate(e=>getComputedStyle(e).opacity)).toBe('1');
  if(route==='docs/'){await expect.poll(()=>page.locator('.docs-nav').evaluate(e=>e.getBoundingClientRect().top)).toBeGreaterThan(86);}
  if(route==='./'){await page.screenshot({path:resolve(shots,'navbar-scrolled-home.png')});await page.locator('.recovery-story').scrollIntoViewIfNeeded();await page.waitForTimeout(750);await page.screenshot({path:resolve(shots,'navbar-over-cream.png')});}
  await page.evaluate(()=>scrollTo({top:0,behavior:'instant'}));await expect(header).toHaveAttribute('data-scrolled','false');await expect.poll(()=>header.evaluate(e=>getComputedStyle(e).backgroundColor)).toBe('rgb(16, 51, 46)');
 }
 await page.goto('docs/#api');await expect(page.locator('#api h2')).toBeVisible();await expect.poll(()=>page.locator('#api').evaluate(e=>e.getBoundingClientRect().top)).toBeGreaterThan(86);
 await page.locator('header nav a').first().focus();await expect(page.locator('header nav a').first()).toBeFocused();
 await page.goto('engine/');await expect(page.locator('main h1')).toBeVisible();const skip=page.getByRole('link',{name:'Skip to content',exact:true});await skip.focus();await expect(skip).toBeFocused();await page.screenshot({path:resolve(shots,'navbar-keyboard-skip.png')});await skip.press('Enter');await expect.poll(()=>page.locator('main h1').evaluate(e=>e.getBoundingClientRect().top)).toBeGreaterThanOrEqual(86);
});
