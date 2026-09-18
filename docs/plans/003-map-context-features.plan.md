# MVP-003 Plan – Map Context Features

Implements [`docs/mvp/003-map-context-features.md`](../mvp/003-map-context-features.md).

**Status:** Superseded during implementation — Phases 1–2 below were built as written
(the `polyconvert` + trimmed type file mechanism), but a real defect (a large coastal
water body `polyconvert` couldn't clip, see `ADR-008`) and, after fixing that, a visually
incomplete rendered map (found by the project owner's own review in `sumo-gui`) led to
replacing the whole shape-rendering pipeline with the project owner's own basemap image
instead. See `ADR-008-basemap-image-for-context-features.md` (renamed from
`ADR-008-polyconvert-for-context-features.md` mid-implementation, reflecting this) and
the MVP's "Outcome at close" for the real story — this plan is kept as-written below for
traceability, not rewritten to match what actually shipped.

## 1. Goal

Make `sumo-gui`'s view of the MVP-002 coverage area show recognisable water and land-use
context, using SUMO's own `polyconvert` tool against the OSM extract already fetched for
the network build — without changing routing, traffic generation, or any headless
simulation output. Every step below was verified for real against this repo's actual
fixtures before being written into a TODO, not assumed from documentation.

## 2. Assumptions

* **Confirmed in this environment, against the real MVP-002 fixtures** (installed
  `eclipse-sumo==1.27.1`, matching the project's pin):
  * `polyconvert` (bundled with `eclipse-sumo`, alongside `netconvert`) reads the same
    `angelholm_bbox.osm.xml` extract `network.py` already fetches, given `--net-file`
    (for coordinate offset/projection alignment with the built network — without it,
    shapes would not line up with the road network in `sumo-gui`), `--osm-files`, and
    `--type-file`.
  * SUMO ships a default OSM→polygon type mapping
    (`<sumo tools dir>/../data/typemap/osmPolyconvert.typ.xml`) — running `polyconvert`
    with it unmodified pulled in **3,363 buildings** plus amenities/shops/parking/etc.
    alongside only 16 water + 52 landuse shapes — far outside MVP-003's scope (buildings
    are explicitly deferred).
  * A **trimmed, custom type file** containing only the water/natural/landuse
    `<polygonType>` entries, combined with `polyconvert --discard` (sets the default action
    for any *unlisted* OSM type to discard, rather than import), produces exactly the
    water + landuse shapes wanted and nothing else — verified by running it for real and
    inspecting the output's `type="..."` attributes (only `water`, `landuse`, `forest`,
    `residential`, `industrial` present, zero buildings).
  * Headless `sumo`, given this `.poly.xml` via `--additional-files`, runs to completion
    unaffected (same step progression, same vehicle count) — shapes are display-only and
    are never read by the simulation engine itself. This is what makes the acceptance
    criterion "MVP-001/002's behaviour is unchanged" a real, checkable property rather than
    an assumption from "it's just visual".
* `polyconvert`'s output is deterministic from its two inputs
  (`network.net.xml` + `angelholm_bbox.osm.xml`), both of which are already committed
  fixtures. This MVP's shapes file therefore does **not** need to be committed either — it
  can be regenerated on every `simulator` run, the same way `generate_traffic()` already
  regenerates routes/`.sumocfg` unconditionally (not just on `--rebuild-network`). It joins
  the existing `apps/simulator/data/*.rou.xml` / `*.sumocfg` / `*.trips.xml` gitignore
  pattern.
* No new pip dependency: `polyconvert` ships with the already-approved `eclipse-sumo`
  package (`ADR-006`). A short new ADR records the polyconvert + custom-type-file
  *mechanism* choice, not a new dependency approval.
* The existing test suite's pattern (mock `subprocess.run`, `tmp_path` fixtures, assert
  constructed argv) is reused as-is.
* `pytest` coverage floor (95%, `ADR-004`) must still hold after this change.

## 3. Proposed file changes

| File | Change |
|---|---|
| `docs/architecture/decisions/ADR-008-basemap-image-for-context-features.md` (new) | Records using `polyconvert` + a custom, discard-by-default type file (not the bundled default, which pulls in buildings) for water/land-use context shapes. |
| `docs/architecture/decisions/README.md` | Add the ADR-008 index row. |
| `apps/simulator/data/context-features.typ.xml` (new, committed) | Trimmed `polyconvert` type file: only water/natural/landuse `<polygonType>` entries, adapted from SUMO's bundled `osmPolyconvert.typ.xml`. Committed (small, static, not regenerated) — unlike the shapes output itself. |
| `apps/simulator/src/simulator/context_features.py` (new) | `build_context_features(osm_file, net_file, output_path, type_file=...) -> Path`, running `polyconvert --net-file ... --osm-files ... --type-file ... --discard -o ...`. Mirrors `network.py`'s `NetworkBuildError`-style error handling. |
| `apps/simulator/src/simulator/traffic.py` | `write_sumocfg()` gains an optional `additional_files: Path \| None = None` parameter, emitting `<additional-files value="..."/>` inside `<input>` when given (relative path, same convention as `net-file`/`route-files`). |
| `apps/simulator/src/simulator/run.py` | After the network is available (rebuilt or reused) and before writing the `.sumocfg`, call `build_context_features()` against the committed `angelholm_bbox.osm.xml` and pass the result into `write_sumocfg(..., additional_files=...)`. |
| `.gitignore` | Add `apps/simulator/data/*.poly.xml` alongside the existing regenerated-output patterns. |
| `apps/simulator/tests/test_context_features.py` (new) | Mocked-subprocess tests for `build_context_features()`, mirroring `test_network.py`'s style. |
| `apps/simulator/tests/test_traffic.py` | New test(s) for `write_sumocfg()`'s `additional_files` parameter (present/absent). |
| `apps/simulator/tests/test_run.py` | Update existing mocks to also patch `simulator.run.build_context_features`; assert it's wired into `write_sumocfg`'s call. |
| `docs/architecture/current-state.md`, `docs/architecture/overview.md` | Update once delivered — new module, ADR-008 reference. |
| `docs/mvp/003-map-context-features.md` | Add an "Outcome at close" section once delivered and verified, following MVP-001/002's pattern. |

## 4. Step-by-step TODO, grouped into phases

### Phase 1 — Commit the trimmed context-features type file

*(commit message: "Add a trimmed polyconvert type file for water/land-use context shapes")*

1. Copy the water/natural/landuse `<polygonType>` entries from SUMO's bundled
   `osmPolyconvert.typ.xml` into `apps/simulator/data/context-features.typ.xml` (already
   drafted and verified in this session — reuse that exact content, don't re-derive it).
2. Re-run `polyconvert --net-file apps/simulator/data/network.net.xml --osm-files
   apps/simulator/data/angelholm_bbox.osm.xml --type-file
   apps/simulator/data/context-features.typ.xml --discard -o <scratch output>` and confirm
   the output's `type="..."` values are exactly `{water, landuse, forest, residential,
   industrial}` (or a similarly small, buildings-free set) — a quick `grep -o
   'type="[^"]*"' | sort | uniq -c` check, same as this session's verification.
3. Write `docs/architecture/decisions/ADR-008-basemap-image-for-context-features.md`
   (Nygard format, matching `ADR-007`'s style) and add its row to
   `docs/architecture/decisions/README.md`'s index.

### Phase 2 — Add `simulator.context_features` and wire it into the config

*(commit message: "Generate and reference context-feature shapes in the simulation config")*

4. Create `apps/simulator/src/simulator/context_features.py`:
   * `DEFAULT_TYPE_FILE` pointing at the committed
     `apps/simulator/data/context-features.typ.xml`.
   * `ContextFeatureError(RuntimeError)`.
   * `build_context_features(osm_file: Path, net_file: Path, output_path: Path, type_file:
     Path = DEFAULT_TYPE_FILE) -> Path`, running `polyconvert` with `--net-file net_file
     --osm-files osm_file --type-file type_file --discard -o output_path`; same
     nonzero-exit / missing-output-file error handling pattern as `network.build_network()`.
5. Extend `traffic.write_sumocfg()` with `additional_files: Path | None = None`; when set,
   write `<additional-files value="{relative path}"/>` inside `<input>`, alongside the
   existing `net-file`/`route-files` lines (same `os.path.relpath` convention).
6. Update `run.py`: after the `net_file` existence/rebuild block, unconditionally call
   `build_context_features(DATA_DIR / "angelholm_bbox.osm.xml", net_file, DATA_DIR /
   "angelholm.poly.xml")` (the OSM extract is always present — it's a committed fixture,
   not gated behind `--rebuild-network`), then pass the result into `write_sumocfg(...,
   additional_files=poly_file)`.
7. Add `apps/simulator/data/*.poly.xml` to `.gitignore`, next to the existing
   `*.rou.xml`/`*.sumocfg`/`*.trips.xml` entries.
8. Write `apps/simulator/tests/test_context_features.py`: success path (mocked
   `subprocess.run`, asserts returned path and that it exists), nonzero-exit error,
   missing-output-file error, and an argv assertion that `--discard` and the type-file path
   are present — mirroring `test_network.py`'s `TestBuildNetwork` structure.
9. Update `test_traffic.py`: a test that `additional_files` given produces the
   `<additional-files .../>` line, and a test that omitting it (existing tests) still
   produces no such line.
10. Update `test_run.py`: patch `simulator.run.build_context_features` in every test that
    reaches `write_sumocfg`; add an assertion that `write_sumocfg` is called with the
    context-features output as `additional_files`.
11. Run `pytest --cov` for `apps/simulator` and confirm the coverage floor still holds.

### Phase 3 — Regenerate the real config and verify no regression

*(commit message: "Regenerate context features for the real network and verify no regression")*

12. Run `simulator` (or call the pipeline functions directly) against the real, committed
    `network.net.xml`/`angelholm_bbox.osm.xml` to generate a real `angelholm.poly.xml` and
    a `.sumocfg` that references it.
13. Inspect the generated shapes file's `type="..."` distribution again against the real
    (not scratch) fixtures — confirm no buildings, a plausible water shape near the Rönneå
    river's known path, and a plausible landuse distribution.
14. Run `simulator --headless` and confirm `"Simulation completed successfully"`, the same
    vehicle count as MVP-002's close (40), and no new errors — this is the concrete check
    that MVP-001/002's acceptance criteria still hold, not an assumption.
15. Run the full `apps/simulator` test suite once more (`pytest --cov`) to confirm nothing
    regressed from the wiring change in `run.py`/`traffic.py`.

### Phase 4 — Verify and close out

*(commit message: "Verify MVP-003 acceptance criteria and close the MVP")*

16. Launch `simulator` (GUI) and visually confirm water and land-use context render
    alongside the road network, in recognisable positions relative to
    `docs/architecture/mapoutline.png`.
17. Project owner visually confirms, in `sumo-gui`, that the area now reads as
    recognisably Ängelholm — the closing acceptance check, not an implementation step.
18. Update `docs/architecture/current-state.md` and `docs/architecture/overview.md` with
    the new module and `ADR-008` reference.
19. Add the "Outcome at close" section to `docs/mvp/003-map-context-features.md`, following
    the MVP-001/002 pattern — record what was actually verified and any real findings.
20. Run the full `pytest` suite one more time before proposing the PR.

## 5. Risks / open questions

* **Type-file completeness.** The trimmed type file only lists the water/natural/landuse
  entries relevant to this MVP's scope; any OSM tag combination not covered falls through
  to `--discard`'s default (dropped, not imported) — safe by construction (nothing
  unexpected leaks in), but if the project owner wants a category this list missed (e.g. a
  specific `natural.*` subtype), it's a one-line addition to
  `apps/simulator/data/context-features.typ.xml`, not a rework.
* **Visual quality is a judgement call.** SUMO's default polygon colors (from the type
  file) are serviceable but generic; if the project owner wants something closer to the
  basemap's own styling, that's a follow-up tuning pass on the type file's `color`
  attributes, not a new mechanism — flagged here so it isn't mistaken for a defect if the
  first render looks plain.
* **Regenerated-not-committed shapes file.** Unlike `network.net.xml`, `angelholm.poly.xml`
  is gitignored and regenerated every run — consistent with the existing routes/`.sumocfg`
  pattern, but means CI/reviewers never see its content directly; the `pytest` coverage and
  the Phase 3 real-fixture inspection are what stand in for that.
* **No change to headless simulation semantics is the whole point** — Phase 3's TODO 14 is
  the concrete gate on that, not a formality to skip if Phase 2's tests pass.
