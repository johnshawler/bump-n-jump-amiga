# Status and next steps

Latest recovered project checkpoint: **034R1 frozen for exact review; emulator validation pending**. No build or emulator was run while preparing this ZIP.

## Evidence boundaries

| Item | Recorded outcome |
|---|---|
| Historical 009 sprite fix | Native endpoint pixels and origin records accepted; logical coordinates preserved. |
| Historical 014 coherent capture | Two source frames each pass 61,440 pixel/coherence checks. |
| Historical 015–019 components | Road step, live movement/cardinal input, clear-road jump and captured terrain contact accepted in their bounded scopes. Old 68000 target. |
| A1200 029 | Startup failed strict AGA gate; preserved. |
| A1200 030 | Plane/guard/palette evidence matched, but restoration failed; no timing acceptance. |
| A1200 031 | Locked Workbench restoration correction; accepted batch comparison recorded as CPU13 versus blitter8 fields per16copies. |
| A1200 032 | Native results independently rechecked; runner failure preserved. |
| A1200 033R1 | Native input/state/planes/DMA/restoration passed separately; overall runner FAILED strict PID absence within deadline. Later cleanup reconciled. |
| A1200 034R1 | Cross-build and host qualification pass; no emulator execution recorded in latest retrieved turn. |
| Physical A1200 | No real-hardware validation established. |

## Current packet identity

- Project root: `G:/Codex/2026-10-18/task-4/bump-n-jump-68000`
- Readiness: `GAME034-A1200-R1-READY.json`
- Request: `build/game034-A1200-R1/REQUEST.json`
- Request SHA256: `e1a6358af3078480f2bff4c5c26e62b0d496bf8a72ca4860b3cbebc954a18dc3`
- Compact descriptor: 259,362 bytes; unchanged reader maximum 262,144 bytes.
- Closure: 256 inputs, 1,373 dependencies.
- Native image: 159,244 bytes; SHA256 `23c140d597a3aa8af8cd8d4418a97f6c8e4f76cbe0fe296d61a57b7fa21b62a9`.
- Recorded recheck command: `python -B tools/check_game034_r1.py` from the original project root. Not executed here.

Do not launch the incomplete `build/game034-STAGING-IMPORT-FAILED` candidate or the oversized pretty-JSON `build/game034-A1200` candidate. The former lacks the runtime-oracle packaging; the latter exceeds the unchanged request-size check. Neither was submitted/granted/run according to the current handoff. R1 preserves qualified native/helper bytes with fresh paths and a compact descriptor.

## Remaining gameplay work

The next bounded milestone is Fire jump → original96-tick landing → no held-Fire retrigger → release → Left steering/contact. The current fixture has a captured map and one proven scroll. Continuous world generation, traffic, crash recovery, audible audio and whole-game timing remain open.

The proposed 034 orderly-close protocol is host-qualified only. It requires an owned WM_CLOSE and held root-HANDLE signal with natural exit0 before residual Job cleanup, then post-exit0, Job0, observer joins and strict root/watchdog absence. It does not identify or prove a cure for the earlier retained process object.

## Suggested next-owner checklist

1. Open current README and HANDOFF-NEXT in the original tree; check for newer work before applying this snapshot.
2. Rehash the complete request closure and reconcile any current launch/result before requesting a new run.
3. Preserve 033R1 as consumed FAIL. Do not rerun it unchanged or turn its separate native pass into overall acceptance.
4. Obtain the workflow's current exclusive admission for the exact candidate; preserve manual sessions.
5. Verify input press/release, source ticks/backlog, exact plane/sprite/palette witnesses and restoration.
6. Accept timing only at the demonstrated granularity and in the exact tested target/scope.
7. Keep physical hardware verification a separately recorded milestone.
