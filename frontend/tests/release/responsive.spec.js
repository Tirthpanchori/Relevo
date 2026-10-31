import {test,expect} from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';
import {mkdir,writeFile} from 'node:fs/promises';
const shots='../.impeccable/review/release-responsive';
test.beforeAll(()=>mkdir(shots,{recursive:true}));
for(const width of [360,390,768,1024])test(`six routes fit and work at ${width}px`,async({page})=>{
 await page.setViewportSize({width,height:900});const errors=[];page.on('pageerror',e=>errors.push(e.message));
 for(const route of ['./','engine/','results/','docs/','about/','privacy/']){
  await page.goto(route);await expect(page.locator('main h1')).toBeVisible();await page.evaluate(()=>document.fonts.ready);
  expect(await page.evaluate(()=>({view:innerWidth,actual:document.documentElement.scrollWidth}))).toEqual({view:width,actual:width});
  await expect(page.locator('header nav a')).toHaveCount(4);
  await page.waitForTimeout(650);await page.screenshot({path:`${shots}/${width}-${route==='./'?'home':route.replaceAll('/','')}.png`});
 }
 expect(errors).toEqual([]);
 await page.goto('engine/#flow');await page.getByRole('button',{name:'Worker stops',exact:true}).click();await page.getByRole('button',{name:'Recovery',exact:true}).click();await expect(page.locator('[data-component=recovery]')).toHaveClass(/active/);
 await page.getByRole('tab',{name:'Replay',exact:true}).click();await expect(page.getByRole('heading',{name:'The task is safely recorded.'})).toBeVisible();
 await page.goto('./#faq');const question=page.getByRole('button',{name:'What is a worker?',exact:true});await question.click();await expect(question).toHaveAttribute('aria-expanded','true');
});
test('mobile model exposes each responsibility and reduced motion shows all explanations',async({page})=>{
 await page.setViewportSize({width:390,height:844});await page.goto('./');await expect(page.locator('[data-anatomy-model]')).toBeVisible();
 const track=await page.locator('#model').evaluate(e=>({start:e.offsetTop,length:e.offsetHeight-innerHeight}));
 for(const [i,t] of [.02,.32,.59,.88].entries()){await page.evaluate(y=>scrollTo({top:y,behavior:'instant'}),track.start+t*track.length);await expect(page.locator('#model')).toHaveAttribute('data-active-level',['coordinator','workers','scheduler','database'][i]);await expect(page.locator('.model-caption')).toBeVisible();await page.screenshot({path:`${shots}/model-${i}.png`});}
 await page.emulateMedia({reducedMotion:'reduce'});await page.reload();await expect(page.locator('.static-levels section')).toHaveCount(4);await expect(page.locator('.hero-pixels canvas')).toHaveAttribute('data-running','false');
});
test('landscape and zoom-sized viewports retain readable model explanations and code keyboard scroll',async({page})=>{
 for(const viewport of [{width:844,height:390},{width:768,height:600},{width:320,height:700}]){
 await page.setViewportSize(viewport);await page.goto('./');await expect(page.locator('h1')).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBe(true);
 if(viewport.height<=650){await expect(page.locator('.static-levels section')).toHaveCount(4);await page.locator('#model').scrollIntoViewIfNeeded();await page.screenshot({path:`${shots}/landscape-${viewport.width}.png`});}
 }
 await page.goto('docs/');const code=page.locator('.code pre').first();await code.focus();await expect(code).toBeFocused();await code.press('ArrowRight');expect(await code.evaluate(e=>e.scrollWidth>e.clientWidth)).toBe(true);
});
test('phone and tablet settled states pass automated accessibility',async({page})=>{
 const report=[];await page.emulateMedia({reducedMotion:'reduce'});
 for(const width of [390,768]){await page.setViewportSize({width,height:900});for(const route of ['./','engine/#flow','engine/#replay','results/','docs/','about/','privacy/']){
 await page.goto(route);await expect(page.locator('main h1')).toBeVisible();if(route==='results/')await expect(page.locator('tbody tr')).toHaveCount(3);if(route.includes('replay'))await expect(page.getByRole('heading',{name:'The task is safely recorded.'})).toBeVisible();
 const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();report.push({width,route,violations:result.violations});}}
 await writeFile('../artifacts/verification/release-responsive-accessibility.json',JSON.stringify(report,null,2));expect(report.flatMap(r=>r.violations.map(v=>({width:r.width,route:r.route,id:v.id,targets:v.nodes.map(n=>n.target)})))).toEqual([]);
});
