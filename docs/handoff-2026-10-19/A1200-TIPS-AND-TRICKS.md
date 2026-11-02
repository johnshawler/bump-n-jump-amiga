# Bump ’n’ Jump: native A1200 tips and tricks

This guide consolidates the recorded development findings from the dedicated **Port Bump ’n’ Jump** task. It is specific to that port, including the fixes that failed before they worked. “Native” below means an Amiga executable tested in an emulator where stated; it does not mean the result was measured on a physical A1200. The source evidence archive accompanies this guide.

## 1. Keep the target and the source timeline explicit

The current target is **stock PAL A1200 / 68EC020 / AGA / 2 MiB Chip / zero Fast or Slow RAM / no FPU, MMU or JIT**. The project directory still ends in `bump-n-jump-68000`; that name is historical. Do not silently restore its old 68000/1 MiB/OCS configuration.

The pinned game source is the **USA NES cartridge**, not an arcade ROM or an established PAL NES edition: CNROM mapper 3/submapper 2, 32 KiB PRG, 32 KiB CHR, NTSC header. Recorded SHA256:

`40e45122fc9ecbda7e94a18c3b4ff6b5022675220872bbc6f02107ec842ce6a6`

The earlier catalogue audit found USA Bump ’n’ Jump and Japanese Buggy Popper, but no European NES edition. That is a recorded search outcome, not proof that no other edition can exist. An Atari 2600 Europe release is not a substitute NES reference. Preserve the original cartridge bytes and verify the hash when resuming.

The approved PAL policy preserves original source simulation speed. Advance input edges, gameplay timers and sound-command sequencing on the source clock; present the latest completed state on each PAL field. Do not change the game to one simulation update per 50 Hz field. The early proposal estimated that about 16.8% of source poses would have no separate displayed image; that is a presentation tradeoff, not permission to drop simulation ticks.

Use an elapsed-time accumulator and retain every due source tick. If execution pauses at crash entry, record the already-due ticks still queued. Test source progression separately from display publication. A four-millisecond polling request is a service request, not a guaranteed latency or performance measurement.

## 2. Translate behavior against the ROM, including its awkward details

Small independent oracles proved more useful than broad claims that the port “looks right.” Retain exhaustive checks for compact state spaces:

| Component | Recorded host coverage | Important rule |
|---|---:|---|
| Input transitions | 65,536 | Preserve original transition semantics. |
| Collision predicate | 65,536 coordinate pairs | Check exact source arithmetic and branches. |
| Normal movement | 131,072 combinations | Source phase gates horizontal movement; Left/Up win over opposites; vertical coordinates wrap. |
| Scroll state | 196,608 cases | Publish current Y before advancing next state. |
| Staged uploads | 8,192 cases | Preserve source dispatch and patch ordering. |
| Clear-road jump | 163,840 cases | Fire edge starts jump; held Fire does not retrigger. |
| Jump pose construction | 192 cases | Check source tile/pose data separately from sprite placement. |
| Terrain contact masks | 16,384 | Check both foot probes and source crash-mode selection. |
| World probes | 32,768 | Preserve the original cache behavior. |

These counts describe the recorded scopes, not a full-game proof. The initial movement audit deliberately called the state bytes `$86` and `$87` until their X/Y mapping was verified. Use the same discipline for newly discovered bytes.

The terrain cache has a source quirk: changing cached row updates the row but leaves cached X untouched until a later call. “Cleaning up” this behavior would change the reference result. The captured-map Left test first touches the boundary at X=79 and enters crash mode 9; that coordinate is fixture-specific.

## 3. Make graphics references coherent before optimizing rendering

Mesen’s end-frame callback was observed to run before the new frame reached its screenshot decoder. A screenshot could therefore describe a different epoch from saved CPU/PPU state. The reference repair used synchronous PPU-frame capture and checked that capture advanced neither CPU, source frame, PPU position nor observed memory.

Keep CPU-side newly built sprite data separate from the PPU’s displayed sprite buffer. At an archived checkpoint those differed. Comparing against the wrong stage can falsely diagnose correct code.

The source viewport is **256×240**, centered without cropping or scaling. Later Amiga display checks use a **320×256, five-plane bitmap**; its 40-byte plane stride gives 51,200 bytes across five planes. Initial diagnostic RGB4 conversion changed individual channels by at most 8/255, but the final palette choice remained open. An exact diagnostic-palette match is not a completed palette decision.

Prepare assets offline: all 2,048 source CHR tiles were checked with lossless local plane/mask data, and the road work built a 32 KiB planar atlas. Keep independent full redraws as the reference for incremental changes.

## 4. Put coordinate corrections at the display boundary

The normal 16×16 car fits one Amiga hardware sprite. The wider 32-pixel jump shapes use **two 16×32 hardware sprites**. The normal-pose asset test matched all 208 opaque source pixels before native placement was accepted.

Run 008 failed because the car was exactly one source pixel too far right at both captured endpoints. Shape, colours and source state agreed; the strict checker still rejected 86 viewport mismatches, or 344 repeated PNG pixels, per image.

The accepted 009 correction kept logical source coordinates unchanged and applied **X−1 only at the pinned V34 `MoveSprite` call**. It added witnesses for logical position, API position, View/ViewPort offsets and sprite DMA words. Both strict endpoint images then matched, with all 51 origin records checked.

Treat X−1 as a fix for that measured API/display path, not a universal AGA rule. Revalidate the mapping under the current A1200/Kickstart path. Never shift expected screenshots or weaken pixel checks to hide a placement error.

Read beam-position data coherently. An early candidate’s separate beam-counter reads could straddle a scanline; it was superseded before launch. If polling hardware counters, prove that the multi-part observation describes one coherent sample.

## 5. Scroll on the source command boundary

The game publishes current Y **before** advancing the next scroll state, wraps at **240 lines**, and supports source advances of **1–4 pixels**. Using the next-state Y at the archived four-pixel checkpoints puts the road four pixels out of phase.

The source NMI command dispatch selects scroll handling with **command bit 0**, verified across all 256 masks. Do not invent one scroll command per PAL field.

The accepted captured frame-700 update contains **18 tile/attribute patches, 236 retained rows and four newly composed rows**. Incremental output matched an independent full redraw byte-for-byte. Continuous world generation was not established by that one correct step.

The retained-row CPU copy became the bottleneck on the old 68000/1 MiB target. Its recorded cost was roughly **80–100 ms**, with the combined pipeline at a **100 ms median / 120 ms maximum**. Those are historical measurements and must not be presented as stock A1200 performance.

The useful replacement is **four overlap-safe descending blits**, followed by completion before the unchanged exposed-strip writer. The host prototype tested 832 guarded five-plane images across 208 geometries, repeated overlaps and 12.3 million word-dependency checks. The prototype driver was 454 bytes plus a 1,664-byte plan table, with no new heap/BSS.

This changes who copies the data, not the bus traffic: the four-pixel path still moves **60,416 Chip-memory read/write bytes**. Account for `OwnBlitter`, command setup, waits, active display DMA and contention. Avoid enabling blitter-hog mode to obtain an unrepresentative result; the verifier rejects it.

On the A1200 031 comparison, the recorded result was **13 serviced fields per 16 CPU copies versus 8 per 16 blitter copies**. This establishes a batch-level advantage under that fixture. It does not establish worst-case update time, a 20 ms deadline, physical bus bandwidth, or full-game FPS. Do not convert it into a per-frame guarantee.

## 6. AGA startup and OS restoration need explicit witnesses

One A1200 startup failed with a chipset byte of `0x13`. The required Alice/Lisa mask remained **`0x0c`**; its internal `0x10` bit was not accepted as evidence of AGA. The correction calls **`SetChipRev(SETCHIPREV_BEST)`** before the strict gate and records the value before, the return value and the value after. A different game’s `19 → 31` observation was corroboration, not Bump’s own proof.

Do not read **BPLCON0** as a correctness witness: it is write-only. FMODE readback was also removed as unsafe. Instead retain readable DMA-enable observations plus OS display-mode witnesses, plane count, bitmap geometry, address bounds and exact plane contents. Label OS witnesses honestly; they are not direct register readback.

Do not require Exec’s managed Chip-memory boundary to equal the nominal physical RAM size. That caused an early false startup failure. Check the effective emulator configuration, allocation success, bounds and non-overlap separately. Current allocation gates must match the 2 MiB target.

`CloseScreen` behavior is version-sensitive. The early Kickstart 1.3/V34 path incorrectly assumed a boolean return; that version returns no value. For the later Kickstart 3.1 diagnostic, the screen-close result was used with additional state checks.

Closing the last screen can reopen Workbench. Run 030 assumed an empty initial screen list must remain empty and failed restoration, despite matching image evidence. The 031 correction establishes and locks a Workbench baseline first, then proves the same screen’s identity/type is restored, the diagnostic screen is removed and the lock is released. Do not weaken restoration checks to accept an unexplained replacement pointer.

Account for all native memory: rounded Hunk allocation, BSS, bitmap, explicit heap, stack, loader and OS resources. The 034 record totals **405,400 bytes for known rounded Hunk + bitmap + heap**, explicitly excluding stack/loader/OS controls. It is not a complete system-memory guarantee.

## 7. Keep jump, terrain and recovery as separate milestones

Fire starts a jump on a press edge. The source clear-road sequence emits sound commands **2, 3 and 4 at ticks 1, 65 and 97**. Command production is not audible audio playback.

The latest 034 slice adds Fire jump, the original 96-tick landing, held-Fire protection, release, resumed Left steering and terrain contact. Its intended directed input includes holding Fire for at least 112 source ticks, witnessing release, then holding Left for 42 source ticks and witnessing release.

The crash audit reaches a wider game-state transition. Do not implement an invented respawn merely to make a demo continue. Current scope remains one proven scroll, captured map, clear traffic and supplied synchronization. Continuous world, traffic, crash recovery, audible audio and complete-game timing are unfinished.

## 8. Measure time at the resolution actually demonstrated

The older timer samples clustered in **20 ms increments**. Apparent one-microsecond operations were unresolved; even empty samples showed about ten raster lines of movement. Clock calibration alone did not establish microsecond accuracy.

A proposed read-only CIAB horizontal-sync sampler was not accepted because shared-latch compatibility with the pinned ROM/OS was unproved. The later harness removed CIA access and counted private VBlank callbacks over 16-copy batches. Do not reintroduce that sampler as a verified trick.

Use the same bitmap and comparable live DMA conditions for CPU/blitter comparisons. The planned ABBAABBA order helps expose ordering effects. Include setup, ownership and completion waits. Measure the combined supported update too: timer/input sampling, game logic, terrain/crash checks, patches, copy, exposed strip, palette and sprite publication. A fast isolated kernel is insufficient evidence for a playable frame budget.

## 9. Keep the freestanding build small and auditable

Cross-compilation and Hunk relocation checks caught concrete problems. A simple I/O length multiplication introduced an unresolved 32-bit runtime helper in the historical 68000 build. Both lengths fit 16 bits, so narrowing the proven-bounded lengths removed that dependency. Keep explicit freestanding memory helpers where the linker requires them; inspect generated code and unresolved symbols.

Use tiny isolated state diagnostics before integrated rendering. The scroll diagnostic streamed vectors through a 24 KiB Chip buffer and built to 2,484 bytes. Historical sizes are useful regression context, not mandatory size limits for the current A1200 executable.

Freeze sources, configuration, executable, verifier, oracle and dependency hashes together. The latest 034R1 native image is recorded as 159,244 bytes, SHA256 `23c140d597a3aa8af8cd8d4418a97f6c8e4f76cbe0fe296d61a57b7fa21b62a9`. Recheck the original file before using it; it is not contained in this ZIP.

## 10. Reliable evidence is part of the engineering

Separate four outcomes: host/oracle checks, guest-native correctness, performance acceptance and whole-run lifecycle acceptance. One may pass while another fails.

033R1 recorded **45 source ticks, 42 held-Left ticks and 34 publications**, with exact planes, DMA and restoration passing independently. Its overall runner still failed because the terminated root object remained queryable through the cleanup deadline. Later process absence, Job0, joins and release were reconciled; the retaining party remains unknown. Preserve the failure.

The 034 host suite covers 9,600 ROM cases, four clock/backlog scenarios, 39 verifier fault rejections, ten actual private Python input/close cases, seven natural-order units and four lifecycle cases, including the full 60-second watchdog. These tests do not constitute execution of the 034 Amiga image.

Two particularly useful harness repairs: latch completion **before** emitting the result and stopping, because a callback may fire again; and treat late pipe-drain errors as failures even when cleanup succeeds. A 026 false PASS was reproduced and the 027 acceptance predicate repaired.

The saved Windows harness uses an exclusive coordinator grant and owned process/window input. Its 60-second execution, 20-second cleanup, 85-second overall and 5-second readiness limits are workflow controls, not Amiga hardware requirements. Root HANDLE signal and Job0 are distinct facts. A terminated object retained by another handle is distinct from a running process and from proven absence. Preserve uncertainty rather than repeatedly launching the same fixture.

Polling disk output is a stop threshold, not a hard storage cap: direct emulator logs bypass a capped stdout reader and can overshoot between samples. The recorded later design discloses an 8 MiB stop threshold, 100 ms sampling and a 16 GiB free-space floor. Earlier quota-volume containment remained unqualified. Do not describe that as a proven hard cap.

## Practical continuation order

1. Recover the original project and rehash 034R1 before changing it.
2. Reconcile current coordinator status; this handoff's latest record has no 034 emulator run.
3. Validate jump → landing → held-Fire protection → steering → terrain contact in the current A1200 configuration.
4. Inspect actual pixels, source-tick traces, DMA/state restoration and clean exit independently.
5. Measure the integrated update under live display DMA, with timing claims limited to the observed resolution.
6. Add continuous world, traffic, source-backed crash recovery and audio in separate checkable increments.
7. Test on a real stock A1200 before making real-hardware or full-speed claims.
