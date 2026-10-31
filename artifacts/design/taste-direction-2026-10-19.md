# DIRECTION SHEET — The product performs
seed 40997419 · drawn 2026-10-19 · sector dev-tool · tone technical
Brief: Relevo: committed job history becomes a readable relay. Preserve user-pinned Griffin hardware breakdown once and use distinct evidence views.

| | |
| --- | --- |
| Direction | The product performs |
| Hero | Fragment on a shaped stage |
| Type | kept from the brand |
| Colour | kept from the brand |
| Sections | intro (Lead line over four columns) ? how-it-works (Drag through the stages) ? showcase (Lit panel, dark row) ? proof (One quiet logo row) ? faq (Question index, one answer) ? footer (A single quiet line) |
| Motion | Shutter image |
| Photographs | the "Architecture" set, as atmosphere |

This is the direction for this build. Adopt it. Do not blend it with the layout you would have made anyway,
and do not redraw because it is unfamiliar: unfamiliar is the point. Redraw a slot only when it conflicts
with a stated brand constraint or needs an asset that does not exist, and say why in your report.

The parts of this sheet were written separately and will disagree in small ways. Settle every disagreement in this order:
**house rules** (including type no smaller than 13px and body text of 16px or more) ? **the direction** (the idea, the composition habits, where the
one accent goes) ? **the type system and the palette** (which face does which job, the five size steps, which colour is the ground and where the
accent goes) ? **the hero blueprint** ? **the section blueprints**. Under each blueprint below, "Adjusted for this page" lists where it disagrees.
In practice: take geometry from blueprints (columns, proportions, what sits where) and take everything else from above them. Map every size a
blueprint names onto one of your five type steps instead of adding a sixth. Use one button shape, one corner radius and one pair of page margins on
the whole page, whatever individual blueprints say. If a blueprint names a kind of typeface (a light serif, a heavy grotesk), use the dealt face.

## 1. The idea
Software is most convincing when it is doing its job in front of you. Instead of describing features, put small, true, working fragments of the product on the page: the actual control, with real content, responding to the pointer. A colour picker's loupe reads the page's own background and prints its value. A list tool lets you tick an item right there. A type-scale plugin sets the page's own headings. Find the one interaction that is the product and make the hero that interaction; then show each further capability as another fragment at real size. No dashboard collage, no browser frame, no screenshots shrunk until unreadable.

Before anything else, write one sentence in your notes: "On this page, <the subject's own material> becomes <the device>."
Fill the first blank from your inventory of what only this client has (its name and what it means, its street, its numbers, its
constraint), then put the nearest competitor in the sentence: if it still works, the idea is the category's, not the client's.
Then name the one live thing the visitor can do on the page (SKILL.md step 4).

## 2. Composition
Hero: a short plain headline (4–6vw, left-aligned, upper-left third) and one sentence; the rest of the first screen is the main fragment at actual interface size, sitting directly on the page or on one flat stage colour, large enough to read every label. The fragment is built in HTML and works. Below, capabilities are a single-column sequence, each a row of two parts on a 5/7 split: a two-line statement on one side and the relevant fragment on the other, with the fragments varying in size and shape so the column never becomes a zigzag of equal blocks. Fragments are cropped pieces of interface (a menu, a row, a control, a panel edge), not whole windows. One section pins a fragment while three short statements change it.

## 3. Type
Kept from the brand. The marketing type matches the product's interface type so the fragments and the page feel like one thing. Headline modest; interface text at its true size (13–15px) inside fragments.

## 4. Colour
Kept from the brand. Neutral ground. The product's own interface colours provide the colour. At most one flat stage colour behind fragments.

## 5. Imagery
**This subject is software and there are no screenshots, so its pictures are its own interface.** Wherever this sheet says photograph, image or object, build a believable fragment of the product in HTML at real size (real labels, numbers that add up, one item hovered or selected), put the attribute `data-ui` on its root, and crop or scale it the way the blueprint treats a photograph: a full-bleed close crop, a tile, the fixed half of a split. Where a fragment makes no sense, use a flat colour field with type on it. Never a fake dashboard of grey bars, never a device frame. If the product works on something physical (ships, plants, buildings, a city), one real picture of that world can carry a section: find it with `node C:/Users/panch/.codex/skills/design-taste-frontend/scripts/assets.mjs "<that world>"`, download it with `--get`, credit it on the page, and never let it pass for the product or its customers.

The interface fragments are the main imagery: build them carefully with real labels, real numbers and sensible states (one hovered, one selected). Around them, two or three real pictures of the customer's world (found with scripts/assets.mjs), never stock of people at laptops.

**Floor (the inspector checks it):** at least four real pictures on the page, usually six to twelve; SVG drawings do not count. One moving picture where an honest clip exists: `node <skill>/scripts/assets.mjs --video "<query>"`, used as a muted loop with a poster frame. Whatever this direction says about pictures, it is carried out with real ones.

Optional atmosphere, two at most, from the "Architecture" set (structure, lines, bridges, facades and building interiors). The page does not need them.
Order of preference for imagery: (1) the project's own photographs and product shots; (2) images you generate, if an image tool is
available; (3) real pictures of the subject's world found in the open collections (assets.mjs, downloaded and credited on the page);
(4) drawings of the subject in code; (5) these. They are real photographs (Unsplash licence, served by picsum.photos) of places, light and
texture. They are atmosphere, never a stand-in for a specific product, dish, person or interface. List the ones you use in your report so
they can be replaced.
- `https://picsum.photos/id/508/1600/1000` — Tall pointed vaults and pale columns of a church interior · light tone · cream, warm grey, soft orange · native portrait · photo: Jeff Sheldon
- `https://picsum.photos/id/954/1600/1000` — Narrow opening in a white wall revealing a white staircase · light tone · off-white, pale beige · calm area: left · native landscape · photo: Todd Quackenbush
- `https://picsum.photos/id/618/1600/1000` — Curving glass and steel lattice roof in black and white · light tone · white, grey, black · black-and-white · native landscape · photo: Mika Ruusunen
- `https://picsum.photos/id/693/1600/1000` — Red suspension bridge tower rising from fog above rugged cliffs · mid tone · rust red, grey, dark teal · calm area: left · native landscape · photo: Rob Bye
The last two path numbers are width and height: request the exact crop you render (`/1200/1500` for a 4:5 portrait, `/2400/1350` for a hero) and
add `?grayscale` to desaturate. Use at most two. Always set `width`, `height`, `alt` and `loading="lazy"` (not on the hero image).
Other sets that fit this brief: sky-and-space, water, texture — `node draw.mjs --photos <set>` prints one in full; `--photos list` shows all sets. Taking photographs from another set is your call and is not a redraw; keep them to one light and one treatment.

## 6. Hero — Fragment on a shaped stage
A neutral ground. The headline occupies the upper-left third: two lines at clamp(52px, 5.2vw, 80px), medium weight, flush left on columns 1–6 at a 40px margin, starting 150px down. One supporting sentence at 18px, max 40ch, follows, then the single action as a small rectangular button. The rest of the screen belongs to one flat stage in a saturated colour: it spans columns 5–12, begins 42% down, and bleeds off the right and bottom edges. Its top-left corner is cut with the product's own shape using `clip-path` (a notch, a chamfer or a tab two columns wide), the only decoration on the page. On the stage, 56px in from its left and top edges, sits the main fragment of the interface at true size with labels at 13–15px, built in HTML and working: one panel or control about 620px wide, cropped by the bottom edge, never a whole window and never inside a browser or laptop frame. Mark its root with data-ui. Navigation is a plain row at 28px from the top: wordmark left and four text links right at 15px. Nothing overlaps the headline.

On a phone: The headline sits under the wordmark at 10vw on two lines, followed by the sentence at 16px and the button. The stage comes next at full width, bleeding off both sides and the bottom, its corner cut kept at 72px wide. The fragment sits 16px inside it at true size; if it is wider than the screen the right edge crops it rather than scaling it down.
Headline: A plain statement of what the product does in three to six words, two lines of up to about 16 characters each at 5.2vw.

## 7. Sections, in order
Each is a composition to rebuild with this project's content. Keep the geometry; change the subject. Re-order or drop a
section when the argument of the page needs it (see references/copy.md), never to fall back to a card grid.

### 1. intro — Lead line over four columns (grid)
Two parts on one 12-column grid with 20px margins. First, a lead paragraph of 30–40 words spans all 12 columns at clamp(22px, 2.2vw, 32px), regular weight, leading 1.2: three lines that read as the opening of a text, with no heading before it. 72px below, four equal columns (three grid columns each, 24px gutters) carry small text at 14–15px with leading 1.45. Each column is one paragraph of 40–70 words that opens with a bold run-in phrase of two or three words in full ink, the rest continuing on the same line in the soft ink. Columns top-align and end ragged at different depths. No cards, icons or dividers; the bold run-ins are the only markers. The four columns answer four plain questions: who, what, where, how to reach them. Padding is modest, 96px top and bottom, so a sheet of images can start straight after.
On a phone: The lead paragraph at 20px, full width. The four columns become a two-by-two grid with a 20px gutter and 40px row gap at 14px; if any paragraph exceeds 60 words, switch to one column with 32px between paragraphs. Run-in phrases stay bold.

### 2. how-it-works — Drag through the stages (split)
A 50/50 split, 88svh tall: two flat fields meeting on a clean vertical edge, and one slider that drives both. Left field: the current stage as a clause of three to six words at clamp(40px, 4.6vw, 76px) on two lines, top-left from column 1, starting with its order word; it serves as the heading. Right field: one fragment of the product at true size, about 440px wide, centred, root marked data-ui, in the state that matches the clause. Along the bottom, crossing both fields inside 28px margins, a real range `<input>` with four stops: a solid track 8px tall, the part already passed in full ink, and a square thumb 32px across in the accent. Under the track, four stage names at 16px, the current one in full ink. Dragging, or the arrow keys, swaps the clause and the fragment's state with a 200ms crossfade; nothing depends on scroll.
On a phone: The fragment's field comes first, 46svh, the fragment at true size and cropped to its active region. The slider follows directly beneath on the seam, thumb 40px. Then the clause field: the clause at 9vw on two lines, with the four stage names under it in a two-by-two block at 15px.

### 3. showcase — Lit panel, dark row (carousel)
One dark field, 96svh tall. Across its middle runs a horizontal row of five to seven interface panels, each a different true-size fragment marked data-ui (an open menu, an inspector, a composer, a chart card), 320–460px wide at their natural heights, vertically centred and 26vw apart. The row scrolls sideways with scroll-snap-type: x mandatory and scroll-snap-align: center, and can be dragged. Only the panel at the centre is lit: full opacity, in the product's light theme, the brightest thing on screen. The others sit at 22% opacity and are inert. The viewport's edges crop the outermost panels. In the gap to the right of the centred panel, top-aligned with it, a 24ch column gives its name at 24px in a light weight and two lines at 16px in a lifted ink; this text changes as panels arrive. There is no heading above the row.
On a phone: The row is 62svh tall; panels snap one per screen at true size, capped at 86vw wide, with neighbours showing 7vw at each side at 22% opacity. The name and its two lines sit beneath the row on the left margin and change with the centred panel. Swiping moves the row.

Adjusted for this page:
- It fades text: anything a visitor reads, inactive items of a list included, is `--ink` or `--muted` at full strength (contrast 4.5:1 or more). The active item is told apart by `--ink` against `--muted`, weight or the accent, not by fading the rest.

### 4. proof — One quiet logo row (strip)
Only for real logos supplied by the project; if none are supplied, set the names in the text face at 22px in the same row and never draw stand-ins. The row reads as a sentence: it opens at the left margin with two to four plain words at 18px (the phrase that introduces the names), vertically centred on the logos, and five to seven logos follow on the same line, spread to the right margin with `justify-content: space-between`. Every logo is normalised to one optical height (28–32px for wordmarks, 36px for compact marks) and one colour, the page ink, using single-colour SVGs with `fill: currentColor`. The band is tall and almost empty: 120–150px of ground above and below the row, no box, no background change and no separate heading. Logos stay still; nothing scrolls or fades at the edges.
On a phone: The opening words sit alone on the first line at 17px. Logos follow in a grid of two per row, each 26px tall and left-aligned in its cell, with 36px between rows. Show six at most; there is no sideways scrolling.

### 5. faq — Question index, one answer (index)
Questions on the left, one answer on the right, and the answer changes as the reader moves through the questions. Columns 1–5 list all questions at one size, 18px, with 18px between them; each is preceded by a solid dot 8px across, in the softer ink when idle and in the accent colour when selected. The selected question is in the full ink, the rest in the softer ink. Columns 7–12 hold the answer pane, `position: sticky; top: 120px`: the selected answer at 24–28px in the regular weight, leading 1.3, measure about 30ch, so the answer, not the question, is the large type. Selection follows hover, click and keyboard focus; the pane crossfades in 150ms. The first question is selected on load. A two-word heading in the softer ink is the first line of the list, at the same 18px.
On a phone: The list runs full width at 18px. Tapping a question colours its dot and opens its answer directly beneath at 19px, indented to line up with the question text; other answers close. There is no pane and no sticky element.

### 6. footer — A single quiet line (strip)
No footer block at all. After at least 30svh of empty page ground, one baseline 30px above the bottom edge carries three items in the page's ordinary small text size (14–16px), the same size and weight as the navigation: at the left margin, what this is in three or four words; centred, two to five links separated by 24px of space; at the right margin, the year and a privacy link. Use a three-column grid (1fr auto 1fr) so the centre group is truly centred whatever the side lengths. No logo, no background change, no line above it, no columns. Links are in the full ink; the rest in the softer ink. If the page has a narrow text column, the three items may instead sit on that column's left edge as one wrapped line. The restraint only works if the page above has already made its invitation.
On a phone: Three short lines at 14px on the left margin with 8px between them: the description, the links on one wrapped line, then year and privacy. Links stay in the full ink. Leave 20svh of empty ground above and 24px below.

## 8. Motion — Shutter image
The one hero or showcase image opens from an edge with a clip-path over about 1.1 seconds while the picture inside settles from 1.12 scale to rest. Use it once, on the image that matters most; later images simply are there. Recipe: 'Image shutter' in references/motion.md.
This is the signature move, the one loud moment. Around it the page still needs the rest of the motion layer (SKILL.md step 9): an entrance for the parts of every section, feedback on every control, and one moving picture. The inspector fails a page that barely moves. Recipes: references/motion.md.

## 9. Where the richness comes from
Fidelity. A fragment with believable content and a real hover state is more interesting than any illustration. Spend the effort there.

## 10. How this direction goes wrong
A fake interface made of grey bars and circles is the worst outcome; if you cannot build a believable fragment, change direction. Mark each fragment's root element with the attribute data-ui: inside it the product's own conventions apply (1px control borders, small radii, a shadow on its open menu) and the inspector leaves them alone; outside it the house rules hold as usual. data-ui is for cropped fragments only, never for a page wrapper. Do not put the fragment in a browser or laptop frame.

## 11. Real references
Studied sites that work this way. Take the principle, never the specifics: no names, copy, images or signature assets of theirs.
- **Uni** (One Page Love, studied score 7.2) `opl-uni`
  Idea: The product lives in the laptop notch, so the page's navigation is a black notch and the hero is a laptop outline whose notch opens into the app.
  Hero: White page with the hero as a rounded-corner panel inset 24px on all sides, filled with a grainy pastel gradient (pink-peach centre, sky blue down the right edge, orange lower-left). A black pill 300×44px sits top-centre like a laptop notch, holding only the app icon; it is the entire nav. Centred below: a hand-scrawled caps eyebrow, a two-line 48px (3.3vw) headline, two white pill download buttons side by side, one line of tiny grey reassurance. The bottom 40% is a thick black outline of a laptop screen, 960px wide, cropped by the fold, its notch expanded into a dark input bar playing the demo.
  Worth taking: Shape the navigation like the product's own hardware habitat (here a black notch pill) so the nav itself demonstrates the product.
- **Shelf** (One Page Love, studied score 7.1) `opl-shelf`
  Idea: Saves scattered across a dozen places are funnelled into one searchable shelf, shown literally by tumbling source chips and a panel edge that narrows to a point.
  Hero: An off-white panel sits inside a 12px warm-grey page frame. A compact floating nav about 880px wide: logo left, three links and a lime waitlist button right. Centred stack: a small grey pill badge with a sparkle icon, then a two-line headline in General Sans Semibold at about 5.8vw with tight tracking, one word of which sits on a lime rounded-rectangle highlight; a two-line grey subhead; an email field with its button nested inside one rounded outline, 460px wide. From 75% down, the top of a bordered app window rises, and a larger search bar holding a half-typed query overlaps it with a soft shadow.
  Worth taking: Shape a section's bottom edge into a chevron and run a hairline from its tip to the next heading, turning 'many into one' into layout.
- **DialKit** (One Page Love, studied score 7.9) `opl-dialkit`
  Idea: The headline is the demo: three floating dial controls from the product sit on top of the sentence and change its weight, spacing and effects live.
  Hero: Near-black viewport with no logo and no nav beyond a two-word audience toggle (active white, inactive grey) in 13px at top-left. A three-line sentence, centred, white, about 9vw with leading near 1.0, occupies the middle 60% of the width and sits optically centred. Three dark glass control chips, each roughly 300 by 80px with large-radius corners, a label on a lighter tab and a monospace value, float over the text at different tilts: one above the first line, one overlapping the start of the last line at lower left, one a segmented off/on switch at lower right. The chips blur the letters beneath them. The bottom third is empty.
  Worth taking: Place the product's real controls on the headline and let them alter the headline's own type settings.
Full notes on any of them: `node draw.mjs --site <id>`.

## Always
Headlines two lines or fewer at every width. No eyebrow labels, no monospace, no 01/02/03, no thin rules, no gradients, no shadows at rest,
no cream-and-terracotta, no violet. `inspect.mjs` measures all of it.

Saved to C:/Users/panch/vscode codes/Relevo/.taste-skill/direction.json · reprint with `node draw.mjs --show`
