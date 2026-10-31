# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: site.spec.js >> desktop accessibility scan of all six pages and both Engine views
- Location: tests\desktop\site.spec.js:140:1

# Error details

```
Error: expect(received).toEqual(expected) // deep equality

- Expected  -  1
+ Received  + 92

- Array []
+ Array [
+   Object {
+     "id": "color-contrast",
+     "nodes": Array [
+       Array [
+         ".model-heading > h2",
+       ],
+       Array [
+         ".model-heading > p",
+       ],
+       Array [
+         ".example-copy > h2",
+       ],
+       Array [
+         ".example-copy > p:nth-child(2)",
+       ],
+       Array [
+         ".example-copy > p:nth-child(3)",
+       ],
+       Array [
+         ".example-note",
+       ],
+       Array [
+         ".sheet-top > span:nth-child(1)",
+       ],
+       Array [
+         ".worker-ticket > div > strong",
+       ],
+       Array [
+         ".worker-ticket > div > span",
+       ],
+       Array [
+         "div[data-reveal=\"recovery-copy\"] > h2",
+       ],
+       Array [
+         "div[data-reveal=\"recovery-copy\"] > p:nth-child(2)",
+       ],
+       Array [
+         ".subtle",
+       ],
+       Array [
+         "li:nth-child(1) > div > h3",
+       ],
+       Array [
+         "li:nth-child(1) > div > p",
+       ],
+       Array [
+         "li:nth-child(2) > div > h3",
+       ],
+       Array [
+         "li:nth-child(2) > div > p",
+       ],
+       Array [
+         "li:nth-child(3) > div > h3",
+       ],
+       Array [
+         "li:nth-child(3) > div > p",
+       ],
+       Array [
+         "div[data-reveal=\"faq-heading\"] > h2",
+       ],
+       Array [
+         "div[data-reveal=\"faq-heading\"] > p",
+       ],
+       Array [
+         "button[aria-controls=\"answer-0\"]",
+       ],
+       Array [
+         "button[aria-controls=\"answer-1\"]",
+       ],
+       Array [
+         "button[aria-controls=\"answer-2\"]",
+       ],
+       Array [
+         "button[aria-controls=\"answer-3\"]",
+       ],
+       Array [
+         "button[aria-controls=\"answer-4\"]",
+       ],
+       Array [
+         "button[aria-controls=\"answer-5\"]",
+       ],
+       Array [
+         "div[data-reveal=\"docs-heading\"] > h2",
+       ],
+       Array [
+         "div[data-reveal=\"docs-action\"] > p",
+       ],
+     ],
+     "path": "/",
+   },
+ ]
```

# Page snapshot

```yaml
- generic [ref=f5e2]:
  - link "Skip to content" [ref=f5e3] [cursor=pointer]:
    - /url: "#main"
  - banner [ref=f5e4]:
    - link "Relevo home" [ref=f5e5] [cursor=pointer]:
      - /url: /Relevo/
      - generic [ref=f5e6]: Relevo Relevo
    - navigation "Main navigation" [ref=f5e9]:
      - link "Home" [ref=f5e10] [cursor=pointer]:
        - /url: /Relevo/
      - link "Engine" [ref=f5e11] [cursor=pointer]:
        - /url: /Relevo/engine/
      - link "Results" [ref=f5e12] [cursor=pointer]:
        - /url: /Relevo/results/
      - link "Docs" [ref=f5e13] [cursor=pointer]:
        - /url: /Relevo/docs/
  - main [ref=f5e14]:
    - generic [ref=f5e15]:
      - heading "A small browser footprint." [level=1] [ref=f5e16]: A smallbrowser footprint.
      - paragraph [ref=f5e17]: What this website requests and stores.Updated 21 October 2026.
    - article [ref=f5e18]:
      - generic [ref=f5e19]:
        - heading "What runs in your browser." [level=2] [ref=f5e20]
        - paragraph [ref=f5e21]: The website serves explanatory pages, self-hosted fonts, and sanitized test evidence. Replay reads a recording. It does not submit work to a live Relevo engine, create an account, or ask for an API token.
        - paragraph [ref=f5e22]: This website has no analytics, advertising, forms that collect personal data, application cookies, or third-party font requests.
      - generic [ref=f5e23]:
        - heading "Preferences and storage." [level=2] [ref=f5e24]
        - paragraph [ref=f5e25]: The website reads your operating system’s reduced-motion preference. It does not save a separate motion preference, playback position, or visitor identifier in browser storage.
        - paragraph [ref=f5e26]: Your browser can cache ordinary site files. Copying a Docs command writes to your clipboard only when you press its Copy button.
      - generic [ref=f5e27]:
        - heading "Hosting and external links." [level=2] [ref=f5e28]
        - paragraph [ref=f5e29]: Your browser requests page files and sanitized evidence from the site’s host. During local development, Vite also connects to its local server for updates. Public deployment remains a separate step; a host may process ordinary request information under its own policy.
        - paragraph [ref=f5e30]: Following a GitHub or design-reference link opens that provider’s website. Its own privacy practices apply. The sanitized recordings contain test identifiers and provenance, with project credentials excluded.
      - generic [ref=f5e31]:
        - heading "Running the engine is separate." [level=2] [ref=f5e32]
        - paragraph [ref=f5e33]: The local Docker application stores tasks and execution history in your PostgreSQL volume. Keep its generated credentials private, use trusted handlers, and avoid sensitive production data in a demo setup.
        - link "Read the local setup guide" [ref=f5e34] [cursor=pointer]:
          - /url: /Relevo/docs/
  - contentinfo [ref=f5e38]:
    - generic [ref=f5e39]:
      - generic [ref=f5e40]:
        - link "Relevo home" [ref=f5e41] [cursor=pointer]:
          - /url: /Relevo/
          - generic [ref=f5e42]: Relevo Relevo
        - paragraph [ref=f5e45]: The worker can change.The work stays accounted for.
      - navigation "Explore footer" [ref=f5e46]:
        - heading "Explore" [level=2] [ref=f5e47]
        - link "Home" [ref=f5e48] [cursor=pointer]:
          - /url: /Relevo/
        - link "Engine" [ref=f5e49] [cursor=pointer]:
          - /url: /Relevo/engine/
        - link "Results" [ref=f5e50] [cursor=pointer]:
          - /url: /Relevo/results/
      - navigation "Build footer" [ref=f5e51]:
        - heading "Build" [level=2] [ref=f5e52]
        - link "Quickstart" [ref=f5e53] [cursor=pointer]:
          - /url: /Relevo/docs/#quickstart
        - link "How it works" [ref=f5e54] [cursor=pointer]:
          - /url: /Relevo/docs/#concepts
        - link "API reference" [ref=f5e55] [cursor=pointer]:
          - /url: /Relevo/docs/#api
      - navigation "Project footer" [ref=f5e56]:
        - heading "Project" [level=2] [ref=f5e57]
        - link "About" [ref=f5e58] [cursor=pointer]:
          - /url: /Relevo/about/
        - link "Privacy" [ref=f5e59] [cursor=pointer]:
          - /url: /Relevo/privacy/
        - link "GitHub" [ref=f5e60] [cursor=pointer]:
          - /url: https://github.com/Tirthpanchori/Relevo
      - navigation "Index footer" [ref=f5e61]:
        - heading "Index" [level=2] [ref=f5e62]
        - link "llms.txt" [ref=f5e63] [cursor=pointer]:
          - /url: /Relevo/llms.txt
        - link "Sitemap" [ref=f5e64] [cursor=pointer]:
          - /url: /Relevo/sitemap.xml
    - generic [ref=f5e66]: Relevo
    - generic [ref=f5e69]:
      - generic [ref=f5e70]: Built by Tirth Panchori · 2026
      - generic [ref=f5e71]: Saved work. Clear history.
      - link "Back to top" [ref=f5e72] [cursor=pointer]:
        - /url: "#top"
```

# Test source

```ts
  49  |  const ids=['coordinator','workers','scheduler','database'];
  50  |  for(const [i,t] of [.02,.32,.59,.88].entries()){
  51  |   await page.evaluate(y=>scrollTo({top:y,behavior:'instant'}),position.start+t*position.length);
  52  |   await expect(model).toHaveAttribute('data-active-level',ids[i]);await expect(page.locator('.level-indicator [aria-current]')).toHaveCount(1);
  53  |   await expect(page.locator('[data-assembly="'+ids[i]+'"]').first()).toHaveAttribute('data-current','true');
  54  |   await expect(page.locator('.model-caption h3')).toBeVisible();const contained=await page.locator('[data-anatomy-model]').evaluate(svg=>{const r=svg.getBoundingClientRect();return [...svg.querySelectorAll('.model-assembly')].every(g=>{const b=g.getBoundingClientRect();return b.left>=r.left-8&&b.right<=r.right+8&&b.top>=r.top-8&&b.bottom<=r.bottom+8;});});expect(contained).toBe(true);expect(await page.locator('[data-assembly="database"]').getAttribute('transform')).toBeNull();
  55  |   await expect.poll(async()=>Math.abs(Number(await model.getAttribute('data-model-progress'))-t)).toBeLessThan(.008);await page.waitForTimeout(180);
  56  |   await page.mouse.move(5,5);await page.screenshot({path:resolve(shots,'model-level-'+(i+1)+'-desktop.png')});
  57  |  }
  58  |  for(const [t,id] of [[.32,'workers'],[1,'database'],[.02,'coordinator']]){await page.evaluate(y=>scrollTo({top:y,behavior:'instant'}),position.start+t*position.length);await expect(model).toHaveAttribute('data-active-level',id);}
  59  | });
  60  | 
  61  | test('hero-only pixel pattern regenerates edge-to-edge and suspends offscreen/hidden',async({page})=>{
  62  |  await page.goto('./');await expect(page.locator('.pixel-band')).toHaveCount(0);const canvas=page.locator('.hero-pixels canvas');await expect(canvas).toHaveAttribute('data-running','true');
  63  |  const before=Number(await canvas.getAttribute('data-frames'));await expect.poll(async()=>Number(await canvas.getAttribute('data-frames'))).toBeGreaterThan(before+2);
  64  |  const data=await canvas.evaluate(c=>{const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let left=0,right=0;for(let y=0;y<c.height;y++)for(let x=0;x<12;x++){left+=d[(y*c.width+x)*4+3]>0;right+=d[(y*c.width+c.width-x-1)*4+3]>0;}return {width:c.clientWidth,viewport:innerWidth,left,right};});
  65  |  expect(data.width).toBe(data.viewport);expect(data.left).toBeGreaterThan(20);expect(data.right).toBeGreaterThan(20);
  66  |  await page.locator('.faq-section').scrollIntoViewIfNeeded();await expect(canvas).toHaveAttribute('data-running','false');let count=await canvas.getAttribute('data-frames');await page.waitForTimeout(180);expect(await canvas.getAttribute('data-frames')).toBe(count);
  67  |  await page.evaluate(()=>scrollTo({top:0,behavior:'instant'}));await expect(canvas).toHaveAttribute('data-running','true');await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});await expect(canvas).toHaveAttribute('data-running','false');
  68  | });
  69  | 
  70  | test('visible fill sweep, press/focus feedback and persistent selected states',async({page})=>{
  71  |  await page.goto('./');const button=page.locator('.home-hero .action');const before=await button.evaluate(e=>getComputedStyle(e,'::before').transform);await button.hover();await expect.poll(()=>button.evaluate(e=>getComputedStyle(e,'::before').transform)).not.toBe(before);await button.focus();await expect(button).toBeFocused();
  72  |  await page.goto('engine/#flow');const selected=page.getByRole('button',{name:'Work completes',exact:true}),other=page.getByRole('button',{name:'Worker stops',exact:true});await other.hover();expect(await selected.evaluate(e=>getComputedStyle(e).backgroundColor)).not.toBe(await other.evaluate(e=>getComputedStyle(e).backgroundColor));
  73  | });
  74  | 
  75  | test('Flow normal/interrupted paths and Recovery highlight; accessible tabs/history',async({page})=>{
  76  |  await page.goto('engine/#flow');
  77  |  await expect(page.locator('.sequence li')).toHaveCount(6);
  78  |  await expect(page.locator('[data-component=application]')).toHaveClass(/active/);
  79  |  await page.getByRole('button',{name:'Task completed',exact:true}).click();await expect(page.getByRole('heading',{name:'The result is saved.'})).toBeVisible();
  80  |  await page.getByRole('button',{name:'Worker stops',exact:true}).click();await expect(page.locator('.sequence li')).toHaveCount(8);
  81  |  await page.getByRole('button',{name:'Recovery',exact:true}).click();await expect(page.locator('[data-component="recovery"]')).toHaveClass(/active/);
  82  |  await expect(page.getByRole('heading',{name:'Make room for another try.'})).toBeVisible();
  83  |  await fullCapture(page,'flow-recovery-desktop.png');
  84  |  const flow=page.getByRole('tab',{name:'Flow',exact:true}), replay=page.getByRole('tab',{name:'Replay',exact:true});
  85  |  await flow.focus();await page.keyboard.press('ArrowRight');await expect(replay).toBeFocused();await expect(replay).toHaveAttribute('aria-selected','true');
  86  |  await flow.click();await page.goBack();await expect(replay).toHaveAttribute('aria-selected','true');
  87  |  await replay.focus();await page.keyboard.press('Home');await expect(flow).toBeFocused();
  88  | });
  89  | 
  90  | test('Replay shows actual steps with aliases, optional exact facts and untimed interventions',async({page})=>{
  91  |  await page.goto('engine/#replay');await expect(page.getByRole('heading',{name:'The task is safely recorded.'})).toBeVisible();
  92  |  await expect(page.getByText(recording.job.id,{exact:true})).not.toBeVisible();
  93  |  await page.getByRole('button',{name:'Next step'}).click();await expect(page.getByRole('heading',{name:'Alex begins the first attempt.'})).toBeVisible();
  94  |  await page.getByRole('button',{name:'Next step'}).click();await expect(page.getByRole('heading',{name:'Ready for another try.'})).toBeVisible();
  95  |  await fullCapture(page,'replay-recovery-desktop.png');
  96  |  await page.locator('summary').click();await expect(page.locator('.technical-content')).toContainText(recording.job.id);await expect(page.locator('.technical-content')).toContainText(recording.events[2].occurred_at);await expect(page.locator('.technical-content')).toContainText('untimed test observations');
  97  |  for(const attempt of recording.attempts)await expect(page.locator('.technical-content')).toContainText(attempt.worker_id);
  98  |  await page.getByRole('button',{name:'Task completed',exact:true}).click();await expect(page.getByRole('heading',{name:'Finished after two attempts.'})).toBeVisible();await expect(page.getByRole('button',{name:'Next step'})).toBeDisabled();
  99  |  await page.getByRole('button',{name:'Play',exact:true}).click();await expect(page.getByRole('button',{name:'Pause',exact:true})).toBeVisible();
  100 |  await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});await expect(page.getByRole('button',{name:'Play',exact:true})).toBeVisible();
  101 | });
  102 | 
  103 | test('Results comparisons reproduce retained measurements and preserve all filters',async({page})=>{
  104 |  await page.goto('results/');await expect(page.locator('.results-table tbody tr')).toHaveCount(3);
  105 |  let row=measurements.repeated.rows.find(r=>r.workload==='short_hash'&&r.workers===1);
  106 |  await expect(page.locator('tbody tr').first()).toContainText(row.baseline.throughput.toFixed(3));
  107 |  await page.getByRole('button',{name:'Confirmation',exact:true}).click();await page.getByRole('button',{name:'Timed tasks',exact:true}).click();
  108 |  await page.getByRole('combobox',{name:'Measurement'}).selectOption('queueP95');
  109 |  row=measurements.confirmation.rows.find(r=>r.workload==='long_timed'&&r.workers===1);
  110 |  await expect(page.locator('tbody tr').first()).toContainText(row.candidate.queueP95.toFixed(1));
  111 |  await expect(page.getByRole('button',{name:'Timed tasks',exact:true})).toHaveAttribute('aria-pressed','true');
  112 |  await fullCapture(page,'results-filtered-desktop.png');
  113 | });
  114 | 
  115 | test('FAQ reverses immediately, closes accessibly and opens one answer at a time',async({page})=>{
  116 |  await page.goto('./');
  117 |  const first=page.getByRole('button',{name:'What does Relevo actually do?'}),second=page.getByRole('button',{name:'What is a worker?',exact:true});
  118 |  await first.scrollIntoViewIfNeeded();await first.click();await expect(first).toHaveAttribute('aria-expanded','true');await first.click();await expect(first).toHaveAttribute('aria-expanded','false');
  119 |  await expect.poll(()=>page.locator('#answer-0').evaluate(el=>el.getBoundingClientRect().height)).toBe(0);
  120 |  await first.click();await second.click();await expect(first).toHaveAttribute('aria-expanded','false');await expect(second).toHaveAttribute('aria-expanded','true');
  121 |  await expect(page.locator('#answer-0')).toHaveAttribute('inert','');
  122 |  await page.locator('.faq-section').evaluate(el=>window.scrollTo({top:el.offsetTop-60,behavior:'instant'}));
  123 |  await expect.poll(()=>page.locator('#answer-1').evaluate(el=>el.getBoundingClientRect().height)).toBeGreaterThan(60);
  124 |  await page.screenshot({path:resolve(shots,'faq-open-desktop.png')});
  125 |  await page.goto('docs/');const button=page.getByRole('button',{name:'Copy terminal commands'}).first();await button.focus();await page.keyboard.press('Enter');await expect(button).toHaveText(/Copied|Select to copy/);
  126 | });
  127 | 
  128 | test('reduced motion has a readable static model, immediate FAQ and manual Replay',async({page})=>{
  129 |  await page.emulateMedia({reducedMotion:'reduce'});await page.goto('./');
  130 |  await expect(page.locator('#model')).toHaveClass(/still/);await expect(page.locator('.static-levels section')).toHaveCount(4);await expect(page.locator('.hero-pixels canvas')).toHaveAttribute('data-running','false');
  131 |  const q=page.getByRole('button',{name:'Can a task still fail?'});await q.click();await q.click();expect(await page.locator('#answer-3').evaluate(el=>el.getBoundingClientRect().height)).toBe(0);
  132 |  await page.goto('engine/#replay');await expect(page.getByRole('button',{name:'Play',exact:true})).toBeDisabled();await page.getByRole('button',{name:'Next step'}).click();await expect(page.getByRole('heading',{name:'Alex begins the first attempt.'})).toBeVisible();
  133 | });
  134 | 
  135 | test('recording/measurement fetch errors and invalid provenance can recover',async({page})=>{
  136 |  await page.route('**/evidence/worker-crash-recovery.json',route=>route.fulfill({status:200,contentType:'application/json',body:'{"events":[]}'}));await page.goto('engine/#replay');await expect(page.getByRole('alert')).toContainText('couldn’t load');await page.unroute('**/evidence/worker-crash-recovery.json');await page.getByRole('button',{name:'Try again',exact:true}).click();await expect(page.getByRole('heading',{name:'The task is safely recorded.'})).toBeVisible();
  137 |  await page.route('**/evidence/benchmark-summary.json',route=>route.fulfill({status:503,body:'Unavailable'}));await page.goto('results/');await expect(page.getByRole('alert')).toBeVisible();await page.unroute('**/evidence/benchmark-summary.json');await page.getByRole('button',{name:'Try again',exact:true}).click();await expect(page.locator('tbody tr')).toHaveCount(3);
  138 | });
  139 | 
  140 | test('desktop accessibility scan of all six pages and both Engine views',async({page})=>{
  141 |  const report=[];
  142 |  for(const path of ['/','/engine/#flow','/engine/#replay','/results/','/docs/','/about/','/privacy/']){
  143 |   await page.goto(path.slice(1)||'./');await page.evaluate(()=>document.fonts.ready);
  144 |   if(path.includes('replay'))await expect(page.getByRole('heading',{name:'The task is safely recorded.'})).toBeVisible();
  145 |   if(path==='/results/')await expect(page.locator('tbody tr')).toHaveCount(3);
  146 |   const result=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();report.push({path,violations:result.violations});
  147 |  }
  148 |  await writeFile('../artifacts/verification/desktop-home-motion-accessibility.json',JSON.stringify(report,null,2));
> 149 |  expect(report.flatMap(row=>row.violations.map(v=>({path:row.path,id:v.id,nodes:v.nodes.map(n=>n.target)})))).toEqual([]);
      |                                                                                                               ^ Error: expect(received).toEqual(expected) // deep equality
  150 | });
  151 | 
  152 | 
  153 | test('Docs follows reading position in both directions and direct fragment loads',async({page})=>{
  154 |  await page.goto('docs/');
  155 |  const nav=page.getByRole('navigation',{name:'Documentation sections'});
  156 |  for(const id of ['quickstart','concepts','api','configuration','evidence','concepts','quickstart']){
  157 |   await page.locator('#'+id).evaluate(el=>window.scrollTo({top:el.offsetTop-100,behavior:'instant'}));
  158 |   await expect(nav.locator('a[aria-current=location]')).toHaveAttribute('href','#'+id);
  159 |  }
  160 |  await page.screenshot({path:resolve(shots,'docs-scrollspy-desktop.png')});
  161 |  await page.goto('about/');await page.goto('docs/#configuration');await expect(nav.locator('a[aria-current=location]')).toHaveAttribute('href','#configuration');await page.reload();await expect(nav.locator('a[aria-current=location]')).toHaveAttribute('href','#configuration');
  162 |  await nav.getByRole('link',{name:'Use the API',exact:true}).click();await expect(nav.locator('a[aria-current=location]')).toHaveAttribute('href','#api');
  163 |  await expect.poll(()=>page.locator('#api').evaluate(el=>Math.abs(el.getBoundingClientRect().top-38))).toBeLessThan(8);await page.waitForTimeout(350);await page.mouse.move(2,2);await page.screenshot({path:resolve(shots,'docs-active-api-desktop.png')});
  164 | });
  165 | 
  166 | test('consistent brand, spacious hero, regenerating pixel grid and reversible report hover',async({page})=>{
  167 |  await page.goto('./');await expect(page).toHaveTitle('Relevo — Background work can recover');
  168 |  await page.evaluate(()=>document.fonts.ready);await expect(page.locator('.footer-word .wordmark')).toBeVisible();
  169 |  const hero=await page.locator('.home-hero').boundingBox();expect(hero.height).toBeGreaterThan(600);
  170 |  const brand=page.locator('.header .brand .wordmark-name'),mask=await brand.evaluate(el=>getComputedStyle(el,'::after').clipPath);
  171 |  await brand.hover();await expect.poll(()=>brand.evaluate(el=>getComputedStyle(el,'::after').clipPath)).not.toBe(mask);
  172 |  await page.screenshot({path:resolve(shots,'hero-brand-hover-desktop.png')});
  173 |  const canvas=page.locator('.hero-pixels canvas');const fingerprint=()=>canvas.evaluate(c=>{const d=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let hash=2166136261;for(let i=3;i<d.length;i+=4)hash=Math.imul(hash^(d[i]>0?1:0),16777619);return hash>>>0;});
  174 |  const grid=await fingerprint();await expect.poll(fingerprint).not.toBe(grid);
  175 |  const stationary=await canvas.evaluate(c=>{const dpr=c.width/c.clientWidth,a=c.getContext('2d').getImageData(0,0,c.width,c.height).data;let offgrid=0;for(let y=0;y<c.height;y++)for(let x=0;x<c.width;x++)if(a[(y*c.width+x)*4+3]>0){const gx=(x+.5)/dpr%5,gy=(y+.5)/dpr%5;if(gx>2.4&&gx<4.6||gy>2.4&&gy<4.6)offgrid++;}return offgrid;});expect(stationary).toBe(0);
  176 |  const paper=page.locator('.report-sheet'),ticket=page.locator('.worker-ticket');
  177 |  await page.locator('.example-section').scrollIntoViewIfNeeded();await page.mouse.move(2,2);await page.waitForTimeout(600);
  178 |  const rest=await paper.evaluate(el=>getComputedStyle(el).transform),ticketRest=await ticket.evaluate(el=>getComputedStyle(el).transform);
  179 |  await paper.hover();await expect.poll(()=>paper.evaluate(el=>getComputedStyle(el).transform)).not.toBe(rest);
  180 |  await page.waitForTimeout(600);await expect.poll(()=>ticket.evaluate(el=>getComputedStyle(el).transform)).not.toBe(ticketRest);
  181 |  await page.screenshot({path:resolve(shots,'report-hover-desktop.png')});await page.mouse.move(2,2);
  182 |  await expect.poll(()=>paper.evaluate(el=>getComputedStyle(el).transform)).toBe(rest);await expect.poll(()=>ticket.evaluate(el=>getComputedStyle(el).transform)).toBe(ticketRest);
  183 |  await page.screenshot({path:resolve(shots,'report-rest-desktop.png')});
  184 |  await page.goto('engine/');await expect(page).toHaveTitle('Relevo — Engine');
  185 | });
  186 | 
  187 | test('hero report example replaces the node diagram and can restart, suspend and reduce motion',async({page})=>{
  188 |  await page.goto('./');await expect(page.locator('.hero-handoff')).toHaveCount(0);
  189 |  const stage=page.locator('.hero-stage'),again=page.getByRole('button',{name:'Run report example again',exact:true});
  190 |  await expect(stage).toHaveAttribute('data-example-stage','4',{timeout:7000});await expect(page.locator('.example-caption strong')).toHaveText('Your report is ready.');
  191 |  await page.screenshot({path:resolve(shots,'hero-complete-desktop.png')});
  192 |  await again.click();await expect(stage).toHaveAttribute('data-example-stage','0');await expect(stage).toHaveAttribute('data-example-stage','1');await expect(stage).toHaveAttribute('data-example-stage','2');
  193 |  await page.waitForTimeout(420);await page.screenshot({path:resolve(shots,'hero-interrupted-desktop.png')});
  194 |  await expect(stage).toHaveAttribute('data-example-stage','3');await expect(stage).toHaveAttribute('data-example-stage','4');
  195 |  await again.click();await expect(stage).toHaveAttribute('data-example-stage','0');
  196 |  await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'));});
  197 |  await page.waitForTimeout(900);await expect(stage).toHaveAttribute('data-example-stage','0');
  198 |  await page.evaluate(()=>{Object.defineProperty(document,'hidden',{configurable:true,value:false});document.dispatchEvent(new Event('visibilitychange'));});await expect(stage).toHaveAttribute('data-example-stage','1');
  199 |  await page.emulateMedia({reducedMotion:'reduce'});await page.reload();await expect(stage).toHaveAttribute('data-example-stage','4');await expect(again).toBeDisabled();
  200 |  const canvas=page.locator('.hero-pixels canvas');await expect(canvas).toHaveAttribute('data-running','false');const frame=await canvas.getAttribute('data-frames');await page.waitForTimeout(250);expect(await canvas.getAttribute('data-frames')).toBe(frame);
  201 | });
  202 | 
  203 | test('Home sections enter on scroll, persist on return and reveal immediately for keyboard/reduced motion',async({page})=>{
  204 |  await page.goto('./');
  205 |  for(const name of ['example-copy','recovery-copy','faq-heading','docs-action','footer'])await expect(page.locator('[data-reveal="'+name+'"]').first()).toHaveAttribute('data-reveal-state','pending');
  206 |  const recovery=page.locator('[data-reveal="recovery-copy"]');await page.locator('.recovery-story').scrollIntoViewIfNeeded();await expect(recovery).toHaveAttribute('data-reveal-state','shown');await expect.poll(()=>recovery.evaluate(e=>getComputedStyle(e).opacity)).toBe('1');
  207 |  await page.screenshot({path:resolve(shots,'recovery-revealed-desktop.png')});await page.evaluate(()=>scrollTo({top:0,behavior:'instant'}));await expect(recovery).toHaveAttribute('data-reveal-state','shown');
  208 |  const docs=page.locator('[data-reveal="docs-action"]');await expect(docs).toHaveAttribute('data-reveal-state','pending');await docs.getByRole('link').focus();await expect(docs).toHaveAttribute('data-reveal-state','shown');await expect.poll(()=>docs.evaluate(e=>getComputedStyle(e).opacity)).toBe('1');await expect(docs.getByRole('link')).toBeFocused();
  209 |  await page.emulateMedia({reducedMotion:'reduce'});await page.reload();await expect(page.locator('[data-reveal-state="pending"]')).toHaveCount(0);
  210 | });
  211 | 
```