# Relevo website design

Created: 2026-10-18 (Asia/Calcutta).

**Status:** the user accepted merging Engine and Replay into one Engine page
with **Flow** and **Replay** tabs (2026-10-18; see D028 in `decision.md`). The
reference roles, compact navigation, short names, and categorized footer are
user requirements. Griffin-inspired pixel/ASCII texture is also an accepted
motif; its exact composition and motion below remain proposals. The remaining
sitemap/content details are proposals.
Palette, typography, detailed compositions, and animation specifications remain
open. No UI implementation or verification is claimed.

Use this file alongside [implementation-plan.md](implementation-plan.md): this
file describes the experience; the plan tracks delivery and verification. Product
truth remains in [PROJECT_MEMORY.md](PROJECT_MEMORY.md), technical rationale in
[decision.md](decision.md), and engine behavior in [working.md](working.md).

## Reference roles

All three references remain relevant; they serve different purposes.

- [Cierto](https://cierto-beta.vercel.app/): overall website structure, explanatory
  content, thoughtful supporting pages, and deliberate light/dark section blocks.
- [Griffin](https://www.griffin.com/): design inspiration for an isometric,
  exploded-view breakdown of the system with scroll-led explanations, plus the
  landing page's pixel-like ASCII/glyph texture, which the user explicitly wants.
- [Etched](https://www.etched.com/): footer inspiration, particularly its detailed
  engineering schematic and strong, spacious closing composition.
- The user's Cierto footer screenshot specifies grouped link columns: Product,
  Evidence, Build, About. Combine that information hierarchy with Etched-inspired
  schematic artwork. Use short page labels and a compact header.
- Choose Relevo's own palette. Neither Griffin's nor Etched's colours are a
  source requirement. Earlier suggested blue/off-white values were proposals.

## Purpose and visitors

Help a backend hiring reviewer or curious developer understand what Relevo does,
how it coordinates work, what happens when a worker fails, and what evidence
supports its claims. Offer a quick overview, then clear routes into detail and
local reproduction. The public experience works with the engine offline.

## Proposed presentation and visitor walkthrough

This elaborates the blueprint for discussion; it does not approve a palette,
font, final composition, or motion specification.

- Use a shared content grid, generous spacing, strong headline hierarchy,
  readable body text, and monospace labels for code, timestamps, and attempt
  details. Concentrate fine-line/grid detail around system illustrations.
- Home uses the light/dark chapter sequence below. Supporting pages inherit
  the same identity while prioritizing diagrams, evidence, or reading according
  to their purpose. Light/dark chapter treatments are separate from any future
  decision about a user-selectable theme.
- Proposed header behavior: remain available while scrolling, show the active
  page, and retain its own readable surface across light/dark chapters. Keep
  the compact Engine/Results/Docs/GitHub layout. The mobile menu exposes the
  same destinations and restores focus to its trigger on closing.
- Home's proposed first screen has the product descriptor and short introduction
  alongside an assembled system illustration. Working headline: "A worker stops.
  Follow the handoff." This copy remains proposed. Primary action Watch replay
  opens Engine's Replay tab; Run locally opens the Docs quickstart.
- The homepage exploded view is a short architectural explanation. Use ordinary
  scrolling to focus the coordinator/durable acceptance, worker execution, and
  independent recovery in sequence while preserving the actual connections.
  Labels identify logical software components rather than physical hardware.
- The normal visitor route is Home -> Engine -> Results -> Docs -> source/local
  reproduction. Direct links must also work for visitors who arrive at any
  supporting page or at the Replay tab without reading Home first.

## Accepted pixel/ASCII motif; proposed execution

The user requested retaining Griffin's pixelated landing-page effect. Browser
inspection confirms the reference uses a canvas-based ASCII-pattern banner:
small characters build a shifting, pixel-like field. This is an additional
visual motif alongside the exploded system view, not a replacement for it.

- Proposed primary placement: a horizontal texture band at the bottom of the
  homepage hero, introducing the transition into the deeper system story.
- Create Relevo's own pattern from code-like glyphs such as `.`, `:`, `+`, `/`,
  `>`, and brackets. Moving clusters can suggest queued signals and handoffs.
  Glyphs are decorative, not actual jobs, telemetry, or recorded events.
- Carry the motif into sparse section-transition details where useful. Keep
  the main text, navigation, charts, and Engine workspace clear and readable;
  preserve the footer schematic's fine-line treatment.
- Colour the effect using Relevo's selected neutral/brand tokens. The proposed
  chalk/graphite/orange palette remains a proposal; this motif does not approve
  it or import Griffin's palette, currency symbols, code, or assets.
- Keep decorative motion slow and bounded. Provide an accessible Pause motion
  control near the effect, a static reduced-motion version, and a useful static
  fallback. Pause rendering offscreen and while the tab is hidden; cap drawing
  density/frame work and verify mobile performance during implementation.
- The effect is decorative and excluded from the reading/focus order. It must
  not obscure controls, capture scrolling, or change the meaning of evidence.
  Renderer, density, timings, and final layout remain open; no effect is built yet.

## Proposed palette - warm chalk, graphite, and burnt orange

**Status:** recommendation for discussion, not user-approved. The colour preview
is a planning illustration, not frontend implementation. Font and composition
choices in the preview do not establish the site's typography or final layout.

| Role | Light chapter | Dark chapter |
|---|---|---|
| Main background | `#F4F1EA` warm chalk | `#14191D` graphite |
| Panel/code surface | `#FFFDF8` paper | `#20272B` raised dark surface |
| Primary text | `#1C2226` ink | `#F3F0E9` chalk |
| Secondary text | `#626B73` | `#A8B1B6` |
| Brand accent/link | `#B84322` burnt orange | `#FF9A72` brighter orange |
| Text on accent fills | `#FFFDF8` | `#14191D` |
| Success label | `#237448` | `#81D3A5` |
| Warning label | `#8C5D0B` | `#EFC773` |
| Failure label | `#B63739` | `#FF9B9B` |

- Keep backgrounds, typography, and most schematic geometry neutral. Apply
  the brand accent to primary actions, selected steps/tabs, and the highlighted
  system path. The brighter dark-chapter accent serves the same brand role.
- Success/warning/failure colours describe state and remain small, labeled,
  and paired with shapes/icons when appropriate. Pending is neutral. Separate
  an active selection from the recorded state of a job or attempt.
- Calculated fourteen specified text/surface pairs using sRGB relative
  luminance. The minimum checked ratio is 4.81:1; primary text is 14.25:1 on
  chalk and 15.55:1 on graphite. Accent/link text is 4.82:1 on chalk and 7.30:1
  on the dark panel. Text on filled accent controls is 5.35:1 / 8.53:1.
- These checks cover exact opaque pairs only, using the
  [WCAG contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).
  UI-state, opacity, chart, diagram, focus, and final rendered contrast checks
  remain part of P8.5. This is not a whole-site accessibility verification.

## Proposed typography

**Status:** recommendation for discussion; not user-approved or installed. The
palette preview inherits the conversation interface's font and uses
`ui-monospace, monospace` for hex labels. It is not a specimen of these families.

| Role | Proposed family | Initial weights | Purpose |
|---|---|---|---|
| Hero and major headings | [Barlow Condensed](https://github.com/jpt/barlow) | 600, 700 | Strong, narrow display typography for the editorial/engineering direction. |
| Body, navbar, controls, Docs | [Instrument Sans](https://github.com/Instrument/instrument-sans) | 400, 500, 600 | Readable continuous text and compact interface labels. |
| Code, diagram labels, timestamps, ASCII glyphs | [IBM Plex Mono](https://github.com/IBM/plex) | 400, 500 | Consistent technical notation and character-grid alignment. |

- These projects publish their fonts under the SIL Open Font License. If the
  proposal is selected, bundle the required webfont files with the site, retain
  their licenses/attributions, and load only needed weights/subsets. Visitors
  and the user do not need a machine-wide font installation.
- Use readable system fallbacks while fonts load. Body text keeps the normal
  sans-serif role; the condensed and monospace faces have focused display and
  technical roles. Verify wrapping, label sizes, fallback layout shifts, code
  alignment, and loading performance during P8.5.
- Family selection, exact sizes/tracking/line heights, and final specimens
  remain pending. No preview or frontend file has been switched to these fonts.

## Sitemap after the accepted merge

**Six content pages: Home, Engine, Results, Docs, About, and Privacy.** This is
the revised sitemap proposal following the accepted Engine/Replay merge. A
custom not-found view is an additional utility screen. Documentation sections
and replay scenarios are anchors/selections within their pages in v1.
The routes below are logical site paths; deployment base/routing is a later
implementation decision.

| Page | Logical path | Visitor's question |
|---|---|---|
| Home | `/` | What is Relevo, and why should I explore it? |
| Engine | `/engine/` | How does execution work, and what happened during actual failure tests? |
| Results | `/results/` | What was measured, under what conditions? |
| Docs | `/docs/` | How can I run, use, and reproduce it locally? |
| About | `/about/` | Why was it built, and why these technical choices? |
| Privacy | `/privacy/` | What does this website request or store? |

## Global navigation

Desktop order:

`Relevo logo | Engine | Results | Docs | [GitHub]`

- Three direct navigation items and one source action. Logo returns to Home;
  Engine opens `/engine/`, Results opens `/results/`, Docs opens `/docs/`, and
  GitHub is the emphasized action opening the actual
  [repository](https://github.com/Tirthpanchori/Relevo).
- The former Proof dropdown is removed from this proposal. Replay is available
  through the Engine tab, the homepage action, and the Evidence footer group.
- About, Privacy, detailed section links, and quickstart are grouped in the
  footer. The Home content retains its Run locally/Watch replay actions.
- Mobile uses a keyboard-accessible menu with the same grouping and a clear
  close action. Show the active page and preserve visible keyboard focus.
- Use readable navigation surfaces across both light and dark sections.

## Home: the complete overview

Background changes introduce chapters. Related sections can share a background;
every scroll movement does not need a colour transition. Specific colours remain
undecided.

| Band | Sections | Content and next action |
|---|---|---|
| Light | Introduction and use cases | Product name, durable task execution description, concise introduction, assembled system preview. Watch replay opens `/engine/#replay`; Run locally opens the Docs quickstart. Explain background, delayed, and retryable work; distinguish integration examples from built-in test handlers. |
| Dark | Inside the engine | Griffin-inspired exploded system view. Separate the coordinator, PostgreSQL, workers/handler processes, and recovery scheduler, with short explanations and actual connection directions. Link to Engine. |
| Light | Follow one job | Explain submission, committed acceptance, claim, execution, and outcome. Show retry returning a job to pending and clarify that expiry belongs to an attempt. |
| Dark | When a worker disappears | A short, clearly labeled preview from the actual worker-crash recording. Explain lease expiry, a replacement attempt, and rejection of the stale report. Link to the Engine page's Replay tab at `/engine/#replay`. |
| Light | Evidence, measurements, boundaries, FAQ | Link to verified tests/CI with revision/date, summarize measured workloads and worker counts, present guarantees alongside limits, and answer the main practical questions. Link to Results and Docs; expose the FAQ at `/#faq`. |
| Dark | Closing action and schematic footer | Run locally/View source actions, a large Relevo wordmark, and the system schematic with grouped footer links. Final footer tone can be revisited with the palette. |

The architectural animation is an explanatory model. Recorded replay is evidence.
Keep those roles and any shortened playback timing visible to the visitor.

The use-case copy should explain background processing, delayed tasks, and
retryable work with concrete examples. Identify hashing, timed work, and
configured transient failures as the implemented handlers. The lifecycle strip
uses the actual pending/running/succeeded/failed states with a retry arrow back
to pending. Evidence summaries identify a source revision and date; 197 backend
tests and 1,440 measured experiment jobs are dated snapshots, not live counters.
FAQ topics include what Relevo executes, what happens after a crash, why effects
can repeat, whether the demonstration is live, and how to run the engine locally.

## Supporting page content

### Engine

- One page with **Flow** and **Replay** tabs, showing one active panel at a time.
  Use a shared diagram workspace with the selected step/event explanation and
  controls. Detailed content should not become two articles stacked together.
- Home's exploded view introduces the components. Engine develops that overview
  through job transitions, ownership details, and actual failure evidence.
- Keep a short guarantees/limits summary below the active workspace. Expand
  deeper technical notes and capture metadata on demand; keep recording labels,
  relevant interventions, and limitations visible when they affect interpretation.
- Use proper tab semantics and keyboard operation. Pause replay when its panel
  is hidden. On narrow screens, stack diagram and explanation naturally rather
  than clipping them into a fixed-height desktop layout.
- `/engine/#flow` and `/engine/#replay` select the corresponding tab. A footer
  link to `/engine/#lifecycle` must select Flow before revealing that content;
  `/engine/#guarantees` targets the shared summary. Test deep links and history
  when implementing routing. These anchors do not add pages.

Proposed workspace order: short page introduction; Flow/Replay tabs; selected
step/scenario controls; diagram beside the current explanation; step/event
timeline; source/details disclosure; shared guarantees/limits summary. Maintain
this one-workspace structure rather than reproducing Home's full introduction.

#### Flow tab

- Begin with an understandable full-system diagram. Explore the API, PostgreSQL,
  worker supervisor/handler, and independent recovery scheduler through labeled
  selections with an accompanying text explanation.
- Trace submit/commit, claim/ownership, heartbeat, outcome, and recovery paths.
  Preserve actual connections: workers communicate through the API; recovery
  operates against PostgreSQL. A stacked illustration is a logical model, not a
  claim that these independent processes form a physical hardware stack.
- Explain jobs versus attempts, the state machine, leases, fencing tokens,
  idempotent submission, bounded retries, and external-effect idempotency.
- Expose Lifecycle and Guarantees sections at `/engine/#lifecycle` and
  `/engine/#guarantees` for direct footer links.
- Include guarantees and limitations at the point they matter, with source links.
- Offer the same comprehension through a static diagram and text. Scroll
  animation must not be required to reach or understand the content.
- A proposed guided sequence is Submit, Save, Claim, Execute, Heartbeat, Finish.
  Each selection explains the relevant component and state change. Show the
  retry/final-failure branch where applicable. Flow is an illustrative model;
  these controls do not submit real jobs or produce measurement evidence.

#### Replay tab

- Three scenario selections: worker crash/recovery; component restarts; duplicate
  business effects with and without stable-key protection. Scenario selections
  share this tab, showing one scenario at a time and reusing existing recordings.
- Pair the system visual with an attempt/event timeline and a plain-language
  explanation of the selected event. Provide play/pause, previous/next event,
  and restart controls accessible by keyboard.
- Show a persistent Recorded test replay label, capture date, source revision,
  configuration/interventions, and links to raw capture and reproduction code.
  Separate recorded facts, explanatory labels, and compressed playback timing.
- Preserve the extra-expiry diagnostic and explain its unassigned cause. Do not
  promise an exact attempt count, recovery deadline, or eventual success.
- Effect recordings explicitly identify direct test lease expiry and the
  instrumented effect transaction. They do not depict a production child holding
  database credentials.
- All interaction is local playback. The public site has no shared API token or
  privileged live controls and needs no running backend.
- Animate recorded events only when supported by the capture. Inferred
  explanations must be labeled as annotations; do not invent individual
  heartbeat events absent from the source. Show actual attempt counts and
  source timestamps, and identify any compressed playback waits.
- The business-effect comparison selects the protected/unprotected recordings,
  preserving their separate provenance. Keep the test lease-expiry intervention
  visible alongside the comparison. Playback ends in a clear finished/paused
  state and can be restarted deliberately.

### Results

- Present workload definitions, 1/3/5-worker comparisons, repeated baseline and
  optional 5 ms tuning results, and the separate confirmation measurements.
- Pair accessible charts with a table; allow workload/worker/variant selection.
  Keep repeated comparisons and one-repeat confirmation visibly distinct.
- Explain throughput, queue delay, attempt duration, and available latency/resource
  observations. Show hardware, software/source versions, run conditions, and raw
  JSON/CSV/source links beside the results.
- Describe 1,440 retained measured jobs as the recorded experiment total, not
  users served or a capacity guarantee. The 0.25-second timed handler waits;
  it is not a CPU-heavy workload. Recorded finish timestamps precede commit ack.
- Keep confounders, excluded-run diagnostics, regressions, and the decision to
  retain the 50 ms default visible. Do not advertise a blanket speedup.
- Proposed reading order: measurement context; workload/experiment selectors;
  worker-count comparison chart and equivalent table; latency/resource detail;
  tuning conclusion; method/limitations; raw data/source links. Repeated runs
  and confirmation are separate selectable datasets, not pooled observations.
- Give charts readable units, sample/repetition context, and text-accessible
  values. Make the source/method available without hover. Details must describe
  the metric actually collected rather than implying continuous live monitoring.

### Docs

- One documentation page with a local contents sidebar/compact mobile contents.
  Initial anchors: Quickstart, CLI and Python client, HTTP API, Configuration,
  Testing and evidence, Observability, Troubleshooting, Guarantees and limits.
- Use `/docs/#quickstart`, `/docs/#cli`, and `/docs/#api` as the short footer
  destinations for Quickstart, CLI, and API.
- Quickstart covers actual prerequisites, local configuration, Compose startup,
  submitting/inspecting a built-in job, and normal stop/restart behavior. Use
  commands verified against README/code before publishing them.
- HTTP API covers all ten actual routes, separating submission/inspection,
  internal worker operations, and health/metrics. Examples use placeholders.
- Explain registered handlers and bounded defaults. Link to actual test,
  recording, and benchmark reproduction instructions and local monitoring.
- Preserve one canonical local setup path; synchronize the site with repository
  instructions rather than inventing a separate browser-based execution flow.
- Use a focused reading layout with a contents sidebar on desktop and compact
  contents navigation on mobile. Group API operations by purpose, including
  the distinction between client job operations and internal worker operations.
- Code examples have Copy controls with visible/accessibly announced feedback,
  placeholder credentials, and platform labels matching verified instructions.
  Troubleshooting should cover configuration, readiness, connectivity, and jobs
  awaiting workers without recommending data deletion as a normal recovery step.

### About

- Explain the project's motivation, the relay/handoff meaning of Relevo, and its
  backend systems portfolio purpose.
- Summarize the actual stack and important tradeoffs: PostgreSQL authority,
  independent workers/recovery, fenced ownership, repeatable effects, and
  recorded public demonstrations. Link to the technical decision log.
- Distinguish completed backend work from remaining delivery work, and identify
  limitations and free-only delivery constraints plainly.
- Include the author's verified GitHub profile and source repository. Credit
  design references and asset/font licenses actually used at `/about/#credits`.
- Proposed reading order: motivation and project purpose; relay/handoff meaning;
  selected engineering tradeoffs; actual stack/status; author/source; credits.

### Privacy and not-found view

- Privacy describes actual site storage, network requests, hosting behavior,
  and third parties after the launch implementation is audited. Do not publish
  unverified no-tracking/no-cookies claims. The planned site needs no sign-in,
  data-submission form, or analytics service to fulfill its purpose.
- The custom not-found view explains the missing destination and links to Home,
  Docs, and the repository. Direct-link behavior must be tested on the chosen
  static host before deployment.

## Shared footer: required content

- Above the links, use Etched-inspired engineering line art depicting Relevo's
  own logical system and connections, with a text equivalent/link to Engine.
- Below the artwork, follow the screenshot's hierarchy: a Relevo identity block
  on the left and four grouped link columns beside it. The identity block has
  the wordmark, A durable task execution engine descriptor, and View source action.

| Product | Evidence | Build | About |
|---|---|---|---|
| Engine | Replay | Quickstart | Project |
| Lifecycle | Results | CLI | Author |
| Guarantees | Tests | API | Privacy |
| FAQ | Checks | Source | Credits |
| | | | llms.txt |
| | | | Sitemap |

- Product destinations: `/engine/`, `/engine/#lifecycle`,
  `/engine/#guarantees`, and `/#faq`.
- Evidence destinations: `/engine/#replay`, `/results/`, the actual repository's
  `backend/tests` directory (Tests), and GitHub Actions (Checks). Raw recordings
  and technical decisions remain linked within the Engine Replay tab and About
  respectively. Replay in the footer is a direct tab link, not a separate page.
- Build destinations: `/docs/#quickstart`, `/docs/#cli`, `/docs/#api`, and the
  GitHub repository (Source).
- About destinations: `/about/` (Project), the verified author GitHub profile,
  `/privacy/`, `/about/#credits`, `/llms.txt`, and `/sitemap.xml`.
- Author attribution via the verified GitHub profile, current copyright year,
  and credits/license links only for actual published resources.
- Concise recorded-evidence note and a Back to top link. The footer is shared
  across all content pages, with visible focus and readable links. On narrow
  layouts, place the identity block first and wrap the four groups into a
  readable two-column or single-column layout.

### LLM overview and sitemap

- The user requires an LLM-readable text file and Sitemap in the footer. Use
  `llms.txt` (the filename in the [public proposal](https://llmstxt.org/); the
  user referred to it as `llm.txt`) and `sitemap.xml`, under the About group.
- Match the user's Cierto screenshot: serve a plain UTF-8 Markdown text file,
  with `# Relevo`, a blockquoted summary, Key facts, and grouped sections of
  descriptive links. It is a readable content file, not just a URL list.
- [llms.txt](llms.txt) is now the repository source draft. It includes Docs,
  Evidence, Results, Project, and Optional sections using existing repository
  resources; no unbuilt website URLs are presented as live. Preserve the
  distinction between explanatory animation and recorded execution and the
  engine's limitations. Link to readable Markdown sources where available.
- `sitemap.xml` will list canonical published content-page URLs using the
  [Sitemaps XML format](https://www.sitemaps.org/protocol.html). Use the actual
  deployment origin and project base path. Tabs/anchors do not become separate
  pages; omit the not-found view and backend/internal endpoints.
- These are two static utility files, not additional content pages. The LLM
  source draft exists; sitemap generation and publication of both remain
  pending. Publish the maintained LLM source through the eventual frontend
  build, refreshing status and real site links at release. Final contents and
  footer URLs must be checked against the production build/actual deployment.

## Open design work and implementation boundary

- Preserve the accepted Engine/Replay merge and Flow/Replay tabs. Remaining
  sitemap/content details stay proposals until settled in the discussion.
- Define Relevo's palette, type, spacing, light/dark treatments, component states,
  illustration geometry, responsive layouts, and motion/fallback behavior next.
- Design the main scene around actual process boundaries and include explicit
  labels for architecture explanation versus recorded execution.
- Continue tracking P8.1 in the implementation plan. It stays open until the
  direction and accessible/responsive interaction model are established.
- No frontend scaffold, UI components, animation code, or deployment is included
  in this draft. Backend evidence remains the authority for public claims.

## Proposed responsive, motion, and feedback behavior

- Desktop places diagrams beside explanations where space allows. Mobile uses
  a single reading order, one active Engine panel, readable diagram labels, and
  touch controls. The homepage breakdown can become a manually stepped figure
  when the full scroll scene would compromise comprehension.
- Reduced-motion mode provides the same information through static scenes and
  explicit step controls. All meaningful interactions work with keyboard and
  visible focus; selected states use text/shape as well as colour.
- Load text and navigation promptly, with a useful static illustration while
  heavier visuals prepare. Preserve the visitor's chosen tab/scenario where
  appropriate; switching away from Replay pauses its playback.
- If a replay or chart dataset cannot load, show a specific readable message,
  a retry action, and direct source/evidence links. Keep surrounding navigation
  and documentation usable. These error states are proposed, not verified UI.
- Footer groups wrap into two columns and then one as necessary. Code blocks
  may scroll horizontally; ordinary prose, controls, and primary diagrams must
  remain readable on narrow layouts.
- Palette, exact font families/sizes, logo geometry, final illustration fidelity,
  motion durations, and detailed breakpoint behavior remain open visual work.
