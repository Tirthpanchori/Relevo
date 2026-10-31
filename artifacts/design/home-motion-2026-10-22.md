# Home motion refinement — 22 October 2026

The latest user steering removes the pixel strip below Home's hero. Keep the
approved Museum palette, Exhibition type, left copy, section order and Anatomy
model. Replace the rejected worker-node animation with a compact report example
on the right. This is a narrow D035 refinement, not a new design-option round.

## Reference observations

Playwright CLI revisited [Cierto](https://cierto-beta.vercel.app/). Its first
Canvas changed pixel fingerprints from 2440828321 to 2190657146 over 600ms.
Its stylesheet defines a `.rise` entrance from opacity 0 / translateY(24px) to
opacity 1 / no translation, with a 0.9-second transition and a reduced-motion
alternative. Those are observed implementation details; they do not imply every
reference section uses the class (the current page query returned none).
The user's screenshot supplies the composition: large copy on the left and a
readable functional example in front of active pixels on the right.
Reference capture: `frontend/.cache/cierto-home-motion-reference.png` (research
only, never shipped). Saved command output remains in the task transcript.

## Motion thesis

On this page, a saved report request becomes the single card that stays present
while an interrupted attempt is replaced. The illustration is labelled and
does not claim the engine currently implements report generation.

- Focal sequence: saved request, preparing, interrupted, another attempt, ready.
  It plays once in 4.7 seconds, can restart manually, and suspends offscreen or
  hidden. Reduced motion shows the complete outcome.
- Continuity: ordinary scroll reveals content groups when reached. The example,
  recorded recovery, FAQ, Docs ending and footer get short entrances. The model
  heading enters, while its four assemblies keep the existing native-scroll
  breakdown. Revealed content stays visible on return.
- Feedback: retain the accepted button, wordmark, card and FAQ feedback. Keyboard
  focus reveals an offscreen action immediately; no content becomes inert merely
  because its entrance has not played.
- Budget: one hero-only Canvas, stationary 5px grid, 2px cells, random occupancy
  and brightness targets every 600ms with local crossfades. Rendering caps at
  24fps and DPR 1.5 and stops offscreen/hidden. No liquid distortion, pointer
  forces, travelling waves, extra strip or new dependency. Density stays lower
  behind the headline and higher behind the example.

Desktop checks and the fresh review are recorded under P8.D8. Tablet/phone work,
responsiveness and publication remain outside this stage.
