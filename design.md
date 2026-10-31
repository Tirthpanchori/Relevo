---
name: Relevo
description: Saved work, clear history - the responsive Museum system.
colors:
  forest: "#10332e"
  paper: "#f3f3dc"
  lime: "#deef59"
  muted: "#486158"
  line: "#cbd0b8"
  soft: "#e7e9d2"
  dark-line: "#34534b"
typography:
  display:
    fontFamily: "Instrument Sans, sans-serif"
    fontSize: "76px"
    fontWeight: 700
    lineHeight: 1.04
    letterSpacing: "-.035em"
  page-title:
    fontFamily: "Instrument Sans, sans-serif"
    fontSize: "68px"
    fontWeight: 700
    lineHeight: 1.03
    letterSpacing: "-.035em"
  headline:
    fontFamily: "Instrument Sans, sans-serif"
    fontSize: "40px"
    fontWeight: 700
    lineHeight: 1.09
    letterSpacing: "-.035em"
  reading-headline:
    fontFamily: "Instrument Sans, sans-serif"
    fontSize: "40px"
    fontWeight: 700
    lineHeight: 1.09
    letterSpacing: "-.035em"
  title:
    fontFamily: "Instrument Sans, sans-serif"
    fontSize: "24px"
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: "-.035em"
  body:
    fontFamily: "Instrument Sans, sans-serif"
    fontSize: "18px"
    fontWeight: 400
    lineHeight: 1.55
  reading:
    fontFamily: "Instrument Sans, sans-serif"
    fontSize: "18px"
    fontWeight: 400
    lineHeight: 1.65
  action:
    fontFamily: "Instrument Sans, sans-serif"
    fontSize: "16px"
    fontWeight: 600
    lineHeight: 1.3
  workspace-title:
    fontFamily: "Instrument Sans, sans-serif"
    fontSize: "32px"
    fontWeight: 700
    lineHeight: 1.09
    letterSpacing: "-.035em"
  hero-lead:
    fontFamily: "Instrument Sans, sans-serif"
    fontSize: "20px"
    fontWeight: 400
    lineHeight: 1.5
  brand:
    fontFamily: "Instrument Sans, sans-serif"
    fontSize: "28px"
    fontWeight: 700
    lineHeight: 1
    letterSpacing: "-.055em"
  code:
    fontFamily: "IBM Plex Mono, monospace"
    fontSize: "14px"
    fontWeight: 400
    lineHeight: 1.85
rounded:
  small: "3px"
  action: "4px"
  fragment: "5px"
  flow: "15px"
  capsule: "30px"
  group: "40px"
spacing:
  group-inset: "4px"
  label-gap: "13px"
  content-gap: "20px"
  action-gap: "22px"
  section-gap: "30px"
  desktop-gutter: "5.5%"
  chapter-gutter: "8%"
components:
  button-primary:
    backgroundColor: "{colors.lime}"
    textColor: "{colors.forest}"
    typography: "{typography.action}"
    rounded: "{rounded.action}"
    padding: "16px 23px"
  button-inverse:
    backgroundColor: "{colors.forest}"
    textColor: "{colors.paper}"
    typography: "{typography.action}"
    rounded: "{rounded.action}"
    padding: "16px 23px"
  button-primary-hover:
    backgroundColor: "#2b5141"
    textColor: "{colors.paper}"
  button-quiet:
    textColor: "{colors.forest}"
    typography: "{typography.action}"
    padding: "6px 0"
  segmented:
    backgroundColor: "{colors.soft}"
    textColor: "{colors.forest}"
    rounded: "{rounded.group}"
    padding: "4px"
  segmented-selected:
    backgroundColor: "{colors.lime}"
    textColor: "{colors.forest}"
    rounded: "{rounded.capsule}"
    padding: "12px 29px"
  select:
    backgroundColor: "{colors.soft}"
    textColor: "{colors.forest}"
    rounded: "{rounded.small}"
    padding: "12px 35px 12px 13px"
  report-sheet:
    backgroundColor: "{colors.paper}"
    textColor: "{colors.forest}"
    rounded: "{rounded.small}"
    padding: "34px 36px"
    width: "350px"
---

# Design System: Relevo

## Overview

**Creative North Star: "The Museum of Saved Work"**

Forest chapters, warm cream reading surfaces and lime signals make background work approachable. Broad Instrument Sans headings and generous left-aligned introductions give the site an exhibition character. An original mechanical rack makes responsibilities tangible; retained records carry the technical proof.

This record describes the shipped six-page desktop implementation: Home, Engine, Results, Docs, About and Privacy. The user selected Museum colours, Exhibition typography/hero, Assembly's model composition and Museum's Engine. Those are regional approvals translated in code, not a claim of whole-comp pixel fidelity; font families were interpreted rather than extracted. Direction seed `0385e4c2` is recorded in `research/cierto-2026-10-21/direction-seed.txt`. The former system/source is archived in `artifacts/design/baseline-2026-10-21-pre-integration`.

**Key Characteristics:**

- Forest and cream chapters with lime task and selection signals.
- Broad sans headings, readable sans evidence, mono for literal technical values.
- Gently rounded actions, capsule selectors and original mechanical depth.
- Native scroll, hero-only random pixel crossfades and reversible state feedback.
- Recorded evidence remains distinguishable from conceptual illustration.

Source authority: `frontend/src/main.jsx` imports `styles.css` followed by `desktop.css`; the last refinement blocks win. Sampled `Surface.jsx`, `PixelField.jsx`, `ScrollReveal.jsx`, `RelayModel.jsx`, `App.jsx`, Home, Engine, Results and Reading, plus `site.mjs`, `public/favicon.svg` and `scripts/prepare.mjs`. Unimported `refresh.css` is not normative. D036 refines the accepted desktop direction: persistent navigation becomes slightly translucent after scrolling, and the hero contains left copy and active pixels only. D035 and `artifacts/design/home-motion-2026-10-22.md` remain historical motion context; D036 removes its hero report example while retaining random hero pixels and content entrances. Desktop scope is widths 1440 and 1920; tablet/phone adaptation and responsive verification remain deferred. Current verification is recorded separately in `artifacts/verification/desktop-navigation-*`; this source-derived record does not assert final check counts or a review verdict.

## Colors

Deep green carries identity and text; cream carries sustained reading; lime marks work, emphasis and selection. Frontmatter preserves the actual reused CSS custom properties.

### Primary

- **Forest:** chapter ground, reading text, default chart bars and inverse actions.
- **Lime:** highlighted words, the persistent task cartridge, active controls, completion marks and closing chapters.

### Neutral

- **Paper:** reading ground and text on forest.
- **Muted:** secondary text on light ground.
- **Line / Dark Line:** contextual boundaries; additional local strokes remain illustration or component details.
- **Soft:** inactive selector and playback surfaces.

### Named Rules

**The Labeled Signal Rule.** Pair active colour with written labels, current/selected state or an explanatory caption; colour alone does not explain execution state.

## Typography

**Display Font:** Instrument Sans (sans-serif fallback).
**Body Font:** Instrument Sans (sans-serif fallback).
**Label/Mono Font:** IBM Plex Mono (monospace fallback) for code and exact technical identifiers; sans for navigation, charts, tables and friendly aliases.

Instrument Sans is locally bundled at weights 400, 500, 600 and 700; IBM Plex Mono at 400. Bold, tightly tracked headings carry the hierarchy without decorative kickers.

### Hierarchy

- **Display / Page title:** frontmatter roles govern Home and other introductions. The Home line is slightly more open; the Engine introduction is centred while the other introductions are left aligned.
- **Headline / Reading headline:** section hierarchy, closing Home chapter and Docs/About/Privacy reading headings share the section size. Engine step explanations use the distinct workspace-title role.
- **Title:** model captions, story headings, worker names, chart headings and Docs subheadings use the supporting role. Some local technical headings retain source-specific sizes.
- **Body / Reading:** narrative, model, evidence and reading paragraphs share the body size; Docs/reading retain the more open reading line height. Hero/page leads use the hero-lead role. General paragraphs cap at (65ch), with local overrides. The cascade retains a general paragraph fallback (19px); it is not the primary narrative role.
- **Action / Label:** actions, playback, navigation, selectors and sequence steps share the control size. Footer metadata is (14px), group headings (16px). Header/footer wordmarks use the brand role; the giant footer scales the same mark. Code and exact identifiers retain the code family.

### Named Rules

**The Reading Hierarchy Rule.** Preserve the smaller reading and workspace hierarchy rather than inheriting the hero's display scale into explanations.

## Layout

The desktop composition was authored at 1100px and above. The release stylesheet overrides body minimum width to zero. Header, hero and workspace use the frontmatter desktop gutter; narrative chapters commonly use the chapter gutter. This is a percentage-based composition, not the former max-width container. The header retains its (86px) layout space and sticks to the viewport top with z-index (100). Narrative chapter vertical padding commonly uses (70–90px); the footer uses (65px) above its groups.

Explanation/art pairs and reading introductions use two-column grids with substantial proportional gaps. Docs pairs a sticky (240px) index with a content column up to (820px); Privacy centres a reading column up to (820px). Tables span their reading surface and code scrolls locally. Footer identity plus four navigation groups precede a large wordmark, capped at (310px) using `min(21vw,310px)`.

The hero uses a (1.35:1) two-column grid with a (5%) gap, a minimum right column (360px), vertical padding (65px) and `min-height:calc(90vh - 86px)`. The right column remains an open pixel field; there is no hero report card or replacement widget. A single Canvas covers the hero background, with lower density behind the left copy. The hero clips its decoration; there is no standalone pixel strip.

The four-level model occupies (210vh) with a sticky interior below the (86px) header, height `calc(100vh - 86px)` and minimum (700px). Its figure is at most (1280px) wide and pairs the drawing with a right-side caption in a (2.4:1) grid, minimum caption width (280px). SVG height is `min(65vh,640px)` with minimum (420px), and camera viewBox is (960 x 640). Reduced motion replaces the scroll track with an auto-height still and all four explanations in a two-column grid; the still SVG is (560px) high. There are no documented tablet/phone breakpoints: the current desktop minimum and deferred scope must remain explicit.

### Responsive release override (1 November 2026)

`responsive.css` is loaded after the desktop stylesheet. Below 1100px the hero uses one column and narrative gutters become 6%. Below 700px the header uses two rows (112px total), narratives and Docs become single-column, footer groups use two columns, and Flow becomes a two-by-two illustration grid. The Flow sequence scrolls locally with keyboard-focusable controls. Docs code blocks remain locally scrollable and keyboard focusable. Results tables retain readable compact cells.

Phone hero type uses clamp(36px,8.9vw,58px); other phone titles use clamp(38px,9vw,55px). Section headings are 30px, main body remains 17–18px. At normal phone heights the four-stage model remains scroll-driven with a 260svh track. At viewport heights of 650px or less, and with reduced motion, a separated still and all four explanations replace the pinned progression. This preserves comprehension on short landscape screens.

Chromium checks cover 320–1920px widths, narrow/short landscape, reverse scrolling, controls, and reduced motion. Real iOS/Android devices and Safari/Firefox are not certified by these checks.

## Elevation & Depth

Reading and workspace surfaces are mostly flat tonal fields with fine rules. Depth belongs to the original rack's shaded planes, bevels, fasteners and diffuse ground shadow, and to the report/ticket illustration. Soft action shadows provide interaction feedback. These are native materials of this world; a universal shadow prohibition would misdescribe the build.

### Shadow Vocabulary

- **Action hover:** `0 6px 16px #001d1920`.
- **Report sheet:** `12px 26px 45px #001c1750`; hover uses `12px 30px 45px #001c1760`.
- **Worker ticket:** `5px 15px 30px #001e182b`; hover uses `5px 19px 32px #001e1838`.
- **Active Flow symbol:** `0 5px 15px #354e1d18`.

### Named Rules

**The Material Depth Rule.** Keep reading and evidence surfaces calm; use shaded mechanical geometry and diffuse shadows where the implemented material or interaction earns depth.

## Shapes

Small corner rounding distinguishes actions and fragments; Flow symbols use a larger soft square. Capsule tabs, filters and playback buttons are deliberate parts of the selected system. Circular dots, sequence terminals and indicators communicate state; the original rack uses rounded mechanical faces. Thin rules structure FAQ, technical details, code, tables and downloads. Inline SVG paths supply functional icons; text glyphs do not substitute for interface icons.

## Components

### Buttons

Primary actions are lime with forest text, inverse actions forest with paper text. Frontmatter gives shared padding and radius. A dark-green fill sweeps upward on hover/focus, text becomes paper, the arrow advances (5px), and the label shifts (-2px) on hover. Press scales the action to (.975). The inverse close sweeps paper into its forest action. Quiet actions use an animated underline and arrow. Global keyboard focus uses a (3px) current-colour outline offset (6px); disabled buttons dim to (.38).

CSS defines press (150ms), hover (240ms) and state (350ms) variables. The shared easing is `cubic-bezier(.16,1,.3,1)`. Hero arrival lasts (500ms), with copy/action delays (70/130ms). Reduced-motion CSS makes transitions and animations zero-duration and removes smooth scrolling and decorative transforms.

### Chips / Segmented controls

Flow/Replay tabs and Results filters sit within soft capsule groups. Lime selected fill persists through hover; inactive hover uses a darker soft fill. Main tabs use frontmatter selected padding; compact filters use (11px 19px). Engine tabs expose tab semantics, arrow-key/Home/End selection and roving focus. Filters expose pressed state. Sequence labels are separate clickable capsule steps with current/passed terminals; hover lifts the label (2px).

### Cards / Containers

The report sheet and overlapping worker ticket are illustrative fragments with soft shadows and gentle rotation. One reversible transform/shadow transition over (550ms), using `cubic-bezier(.22,.61,.36,1)`, lifts and straightens them without implying navigation. The sheet changes from (-6deg) to (-3deg), adds (-5deg) Y rotation and rises (9px); the ticket changes from (3deg) to level while moving (7px,-5px). The earlier scroll-linked paper keyframe is disabled, so hover exit returns smoothly. Reduced motion retains the resting rotations. Reading and evidence containers remain mostly flat. About's original relay poster is a distinct CSS composition, not a reusable dashboard card. Results row/table hover adds a pale green ground; bar hover slightly increases brightness.

### Inputs / Fields

The Results measurement control is a native select with soft fill, fine line border, small radius and (16px) text. It uses the shared visible focus outline. No text-entry, validation or error-field system is established.

### Navigation

The header explicitly includes Home, Engine, Results and Docs. It stays visible at the top while scrolling. A passive scroll listener marks the scrolled state above (12px): solid forest changes to `rgb(16 51 46 / .9)`, with (10px) backdrop blur and a subtle `rgb(243 243 220 / .12)` bottom rule. Only the surface becomes translucent; links and wordmark stay opaque. Background and border transitions take (240ms) with the shared easing; reduced motion removes them. Links use (16px) type; current page uses lime plus an underline, hover reveals the underline. The shared canonical Relevo wordmark and proportional lime dot appear in header/footer/About. Header/footer brand links use the frontmatter brand role. The lime name overlay sweeps across via clip-path over (420ms) on hover, keyboard focus and press; the dot shrinks to (.8) and turns paper on hover/focus. Press moves the link down (1px). Browser titles start with Relevo; the SVG favicon pairs a cream R and lime dot on forest. Footer groups are Explore, Build, Project and Index; links move slightly and turn lime on hover. Docs uses a lime current-location fill, forest text and semibold weight, with (13px 14px) link padding and (4px) corners. The sticky Docs index sits (112px) from the viewport top and article sections use a fragment scroll margin (124px), clearing the header. Its active section follows a reading line at `min(180px,22vh)` through requestAnimationFrame-throttled scroll/resize detection. Cold fragments align after DOM/font readiness; upward scroll and fragments update selection without rewriting history on each scroll. A keyboard skip link appears at focus above the header at z-index (110); its main-content target has a scroll margin equal to the header height (86px), keeping the destination clear. On phones the header is 112px tall with the brand above all four visible navigation links.

### Typographic hero

The left headline, short explanation and single Engine action sit over the active pixel background. Lime emphasizes ?recover?; the open right field carries denser pixels. D036 removes the report animation and card from this viewport. The separate lower report/ticket scene remains a labelled example of a possible integration, with its existing reversible material feedback.

### Content entrances

Home's example, recorded-recovery, FAQ and Docs-ending content groups, the model heading and footer navigation group reveal once when reached. Only groups initially below the viewport's (65px) bottom inset are armed; content already in view remains visible. Entry fades and rises (24px) over (650ms), using the shared easing and a paired delay (100ms). Revealed groups stay visible on return. Keyboard focus reveals immediately without delay; reduced motion leaves all groups visible. Normal section backgrounds and layout remain in document flow. The footer mounts with the loaded page inside Suspense, so its entrance is measured at its actual page position. The model assemblies retain their separate native-scroll sequence.

### Four-level rack and pixel field

The original SVG rack reveals Coordinator, Workers, Recovery and Saved record in sync with native scroll. Geometry, current indicator, signal faces and caption change together; reverse scrolling retraces the same sequence. The task cartridge stays with storage; storage never independently translates. Assembly bounds are cached at mount or motion-preference change, then translated bounds fit the camera on each scroll update. A bounded spring (stiffness110, damping26, mass.5) smooths native scroll; separation occurs across roughly the first (69%) of each quarter before a hold. Mount-aligned dashed guides explain the raised assembly; the worker rail also shifts slightly. Inactive assemblies stay opaque with reduced saturation. The reduced-motion still separates assemblies and displays all four explanations. Projection primitives are sourced and licensed in `frontend/src/anatomy/NOTICE.md`; geometry and renderer are original. There are zero shipping rasters.

The single decorative hero Canvas draws (2px) cells on a stationary (5px) grid. Occupancy and brightness targets regenerate every (600ms) and crossfade locally; there is no liquid deformation, travelling wave, pointer force or pointer listener. Density rises toward the open right field using `(.006 + .75 * (x / width)^3.5) * (.55 + patch)`, keeping the left copy quieter. Rendering caps at (24fps) and device-pixel ratio (1.5), suspends offscreen/hidden and draws a reduced-motion still. It carries no embedded sentences, global pause button or saved preference.

### Engine, evidence and code

Flow starts with explicit Application submission and uses six normal or eight interrupted steps. The current responsible symbol receives lime fill and a matching border; Recovery highlights during interrupted recovery and is explicitly labelled standing by on the normal path. Replay shows two recorded attempts in distinct worker lanes. Friendly aliases do not replace the exact identifiers available in optional technical details. Replay width transitions last (400ms); step copy fades over (220ms). MotionConfig respects the user's motion setting, and explicit reduced-motion branches remove geometric motion. Replay starts paused, disables Play for reduced motion, stops on document hiding and permits manual stepping. Evenly spaced steps are accelerated exposition, not a wall-clock reconstruction.

Results pairs bars with a real table and labelled controls. Provenance, measurement conditions and raw downloads stay accessible. Code uses a dark green fragment, mono text, horizontal overflow and copy feedback. Technical details use native disclosure. Evidence-load failure offers retry. The public site fetches retained local artifacts, not a privileged live engine.

### FAQ

One answer opens at a time with button expanded state, linked labelled region and inert closed content. Motion animates height and opacity reversibly over (340ms), using the shared easing; the drawn plus becomes a minus. Hover adds a pale ground. Reduced motion removes the transition.

## Do's and Don'ts

### Do:

- **Do** preserve forest/cream chapters and lime signals with explicit labels and selected states.
- **Do** keep the broad sans hierarchy and readable evidence beside its conditions.
- **Do** retain capsule selectors, gently rounded fragments and the original model's material depth.
- **Do** keep native scroll, manual Engine stepping and static reduced-motion explanations usable.
- **Do** distinguish illustration, accelerated playback and retained measured evidence.

### Don't:

- **Don't** infer public deployment, real-device certification or whole-comp fidelity from local browser tests.
- **Don't** add decorative kickers, glyph interface icons, system-font display headings or hard offset interface shadows.
- **Don't** make animation or a live backend necessary to understand the site.
- **Don't** invent execution guarantees, timestamps, measurements, customers or exactly-once claims.

Not canonized or repaired: superseded stylesheet declarations and unimported refresh.css remain historical residue, not current rules; tablet/phone layouts remain explicitly deferred. The illustrative-example caption identifies provenance rather than establishing a decorative kicker style. Removed worker-node, hero-report and pixel-band components are not current rules. No UI repairs or unverified review verdicts are introduced by this documentation pass.
