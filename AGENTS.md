# Relevo project instructions

Read `PROJECT_MEMORY.md` before planning or implementing work in this repository.
It records the user's accepted scope, stack, constraints, and implementation direction.
Update it when the user changes a decision or a milestone is completed. Preserve the
distinction between planned capabilities and verified implementation.

Before implementation, read `README.md`, the current phase and gates in
`implementation-plan.md`, and the relevant entries in `decision.md`. Use
`working.md` for the behavior explanation. Verify documentation claims against
actual code, configuration, and tests when those exist.

- Keep phase/task IDs stable and add actual verification evidence before marking
  work complete in `implementation-plan.md`.
- Append important technical tradeoffs to `decision.md`; link replacements when
  superseding a decision. Update `working.md` for behavior changes and `README.md`
  for verified setup changes in the same change.
- Implement the backend first. Do not begin frontend implementation until the
  plan's backend readiness gate passes.
- The user requires a conversation before frontend work, even after the gate
  passes. Continue only through Phase 7 until that discussion happens.

- Backend: Python. Frontend: React with JavaScript and Vite; use `.jsx` and `.js`.
- Handle project dependency downloads/installation as needed. Check existing
  tooling first and tell the user when a separate PC application, system setup,
  or restart requires their action. Prefer project/container dependencies over
  unnecessary machine-wide installations.
- Deployment must be free-only: recurring budget is INR 0. Do not substitute paid
  hosting or time-limited trial credits for an ongoing free deployment.
- Prioritize the executor's correctness, recovery tests, and measured behavior.
  The frontend explains the engine and its evidence.
- Do not claim exactly-once execution, guaranteed uptime, real-user adoption, or
  benchmark results that the implementation has not demonstrated.
