# Changelog

## 0.3.0a4 - 2026-06-20

This alpha preview packages the Phase 3 calibrated pressure baseline for controlled human playtesting while pressure director refinement continues.

### Added

- Release-candidate build artifact workflow support.
- Phase 3x pressure playtest checklist for controlled tester feedback.
- Regression coverage for calibrated pressure constants and non-boss pushback wiring.

### Changed

- Medium difficulty now uses the calibrated 89.0 capture threshold while Easy and Hard retain the 5.0 fallback threshold.
- Non-boss destruction pushback now uses the configured 0.255 multiplier.
- Package version metadata updated to 0.3.0a4.

### Fixed

- Calibrated capture pressure now applies as Medium-specific tuning rather than a global Easy/Hard behavior change.
- The start notification now displays the active difficulty's capture threshold dynamically.

## 0.3.0a3 - 2026-06-14

### Added
- Added regression tests for runtime window branding application, PRC configuration generation, and early startup splash overlay lifecycle ordering.

### Fixed
- Fixed runtime application of window title and icon immediately after ShowBase construction.
- Implemented an aspect-aware, early startup splash overlay that renders before assets load and hides once the main screen is ready.

## 0.3.0a2 - 2026-06-14

### Added

- Regression tests for pause overlay visibility, pause copy source of truth, and startup branding generation.

### Fixed

- Restored pause overlay help text visibility on repeated pause entries.
- Updated startup splash and icon to use the main-menu title logo as the canonical source.
- Ensured derived startup branding assets regenerate to avoid stale icons/splashes.

## 0.3.0a1 - 2026-06-14

This alpha preview starts the `0.3.x` automated gameplay calibration line.

### Added

- Automated gameplay calibration target-band reporting for key skill and difficulty pairs.
- Critical-gap-duration and near-death-event metrics in calibration output.
- Matrix report target-band review output for calibration runs.
- Optional quick and full matrix readiness gates for gameplay-affecting changes.
- Branded startup splash and generated game icon derived from the main-menu logo family.
- Shared UI text/button autofit policy for current and future screen widgets.

### Changed

- Updated package version metadata to `0.3.0a1`.
- Clarified roadmap/version labels so `0.3.x` remains gameplay calibration and `0.4.x` remains progression/playable content.
- Updated Escape behavior so it exits only from the main menu, backs out of menu subscreens, preserves the settings-save prompt, pauses active play, and resumes from pause.
- Updated screen construction so owned labels/buttons run through shared text-fitting safeguards.

### Fixed

- Fixed a Victory screen synchronization issue when Executive Decision defeats the dreadnought.
- Fixed result-screen message overflow by wrapping and fitting Victory/Game Over text inside its panel.

## 0.2.0a2 - 2026-06-14

This alpha preview supersedes `0.2.0a1` with runtime launch fixes, broader visual runtime validation, and multi-platform release packaging preparation. It is not a 1.0 release and does not claim the full planned game scope is complete.

### Added

- Visual runtime validation for active enemies, projectiles, pickups, visual effects, and presentation synchronization.
- Windows, Linux, and macOS release ZIP packaging preparation.
- Release workflow gates for visual runtime checks before packaged builds are published.

### Changed

- Updated package version metadata to `0.2.0a2`.
- Updated release packaging to prepare all configured desktop platform ZIPs.
- Updated release publishing so the same packaged assets can be attached to both the source and public releases.

### Fixed

- Fixed pickup rendering during active gameplay.
- Fixed pickup texture selection during active gameplay.
- Fixed enemy trail rendering during active gameplay.
- Fixed release readiness coverage for visual runtime interface mismatches.

## 0.2.0a1 - 2026-06-12

This alpha preview packages the post-Phase-5 gameplay foundation. It is not a 1.0 release and does not claim the full planned game scope is complete.

### Added

- Data-driven foundations for ships, equipment, player profile/inventory, maps, story nodes, quests, rewards, progression logging, and event-pack manifests.
- Story popup presentation, post-run quest integration, reward grant foundations, and replay-oriented story/quest planning.
- Accessibility-scale layout checks for settings and dynamic button text.
- Public source snapshot publication for the alpha preview.

### Changed

- Updated package version metadata to `0.2.0a1`.
- Tightened the public source snapshot to include only runtime/source/package files and public-facing prose.
- Improved release packaging compatibility with current setuptools validation.

### Fixed

- Fixed settings layout regressions where long dynamic labels could overflow visible button text.
- Fixed public snapshot validation for generated preview contents.
- Cleaned copied runtime files for the public alpha preview.

## 0.1.1 - 2026-06-01

### Added

- Curated sprite alpha normalization and validation checks.
- Regression coverage for generated/curated asset boundaries and orientation behavior.

### Changed

- Scoped strict transparent-pixel checks to tracked curated sprites.
- Improved actor visual turning behavior for player and enemy movement.

### Fixed

- Cleaned curated UI frame transparency.
- Removed obsolete UI texture references from active presentation paths.

## 0.1.0 - 2026-05-29

Initial public prototype milestone with responsive UI/HUD work, curated image pipeline foundations, and Windows release build preparation.
