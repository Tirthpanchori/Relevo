These paired runs used the same `b84be4e` runtime image. A later audit found that
its server logging setup inadvertently re-enabled access logging despite the CLI
flag; that behavior was corrected after these measurements. Both paired variants
shared the issue. These remain measurements of the recorded revision, not a
capacity claim for later revisions.

The decision remains conservative: keep the 50 ms default. The 5 ms setting is an
optional short-task tuning mode with validated correctness and explicit measured
regressions for timed work. One confirmation case per group is descriptive;
consult the earlier three-repeat matrix and raw measurements as well.
